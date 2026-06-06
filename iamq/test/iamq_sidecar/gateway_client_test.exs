defmodule IamqSidecar.Gateway.ClientTest do
  @moduledoc """
  Tests for `IamqSidecar.Gateway.Client` — the WebSockex-based gateway
  notifier used by the main agent's IAMQ hook.

  Coverage strategy:
  - The public `send_telegram/1` is tested for the paths that don't need
    a real WS transport (no_token, WS failure -> CLI fallback, CLI
    failure -> inbox fallback).
  - The WebSockex lifecycle (start_link, handle_connect, handle_frame,
    handle_disconnect) is exercised by calling the callback functions
    directly with synthesized state and frames.
  """
  use ExUnit.Case, async: false

  alias IamqSidecar.Gateway.Client

  @moduletag :gateway

  # `caller` is computed per-test via setup so it points at the running
  # test pid (not the compile-time pid, which is what `self()` would
  # capture if we used a module attribute).
  defp base_state(caller) do
    %{
      gateway_url: "ws://127.0.0.1:18789/ws",
      token: "test-token",
      delivery_payload: %{
        account: "oc_gr_mq_bot",
        channel: "telegram",
        content: "hello",
        deliver: true,
        target: "5887382088"
      },
      caller: caller,
      req_id: 1,
      status: :idle
    }
  end

  setup do
    prev_token = System.get_env("OPENCLAW_GATEWAY_TOKEN")
    prev_url = System.get_env("OPENCLAW_GATEWAY_URL")
    prev_account = System.get_env("OPENCLAW_TELEGRAM_ACCOUNT")
    prev_home = System.get_env("HOME")

    System.put_env("OPENCLAW_GATEWAY_TOKEN", "test-token")
    System.put_env("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789/ws")
    System.put_env("OPENCLAW_TELEGRAM_ACCOUNT", "oc_gr_mq_bot")

    on_exit(fn ->
      if prev_token, do: System.put_env("OPENCLAW_GATEWAY_TOKEN", prev_token), else: System.delete_env("OPENCLAW_GATEWAY_TOKEN")
      if prev_url, do: System.put_env("OPENCLAW_GATEWAY_URL", prev_url), else: System.delete_env("OPENCLAW_GATEWAY_URL")
      if prev_account, do: System.put_env("OPENCLAW_TELEGRAM_ACCOUNT", prev_account), else: System.delete_env("OPENCLAW_TELEGRAM_ACCOUNT")
      if prev_home, do: System.put_env("HOME", prev_home), else: System.delete_env("HOME")
    end)

    {:ok, state: base_state(self())}
  end

  # --- send_telegram/1: no_token short-circuit ----------------------------

  describe "send_telegram/1 — token" do
    test "returns {:error, :no_token} when OPENCLAW_GATEWAY_TOKEN is unset" do
      System.delete_env("OPENCLAW_GATEWAY_TOKEN")

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:error, :no_token} = Client.send_telegram(%{"subject" => "hi"})
        end)

      assert log =~ "OPENCLAW_GATEWAY_TOKEN not set"
    end
  end

  # --- send_telegram/1: CLI fallback paths --------------------------------

  describe "send_telegram/1 — CLI fallback when WS RPC fails" do
    setup do
      :meck.new(WebSockex, [:passthrough])
      :meck.expect(WebSockex, :start_link, fn _url, _mod, _state, _opts ->
        {:error, :not_connected}
      end)
      on_exit(fn -> :meck.unload() end)
      :ok
    end

    test "CLI fallback returns :ok when System.cmd succeeds" do
      :meck.new(System, [:passthrough])
      :meck.expect(System, :cmd, fn "openclaw", _args, _env ->
        {"delivered", 0}
      end)
      # The setup's on_exit (:meck.unload()) will unload System too.
      # Adding a per-test on_exit would race with it.

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert :ok = Client.send_telegram(%{"subject" => "hi", "from" => "x"})
        end)

      assert log =~ "CLI fallback succeeded"
    end

    test "CLI fallback writes to inbox when System.cmd exits non-zero" do
      tmpdir = Path.join(System.tmp_dir!(), "gateway_test_#{System.unique_integer([:positive])}")
      File.mkdir_p!(Path.join([tmpdir, ".openclaw", "workspace", "queue", "main"]))
      System.put_env("HOME", tmpdir)

      :meck.new(System, [:passthrough])
      :meck.expect(System, :cmd, fn "openclaw", _args, _env ->
        {"", 1}
      end)
      on_exit(fn ->
        :meck.unload()
        File.rm_rf!(tmpdir)
      end)

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert :ok = Client.send_telegram(%{"subject" => "inbox-fallback", "from" => "x"})
        end)

      assert log =~ "inbox fallback"

      inbox_path = Path.join([tmpdir, ".openclaw", "workspace", "queue", "main", ".pending"])
      assert File.exists?(inbox_path)
      body = File.read!(inbox_path)
      assert body =~ "inbox-fallback"
    end

    # Inbox fallback itself can fail (L140). We force File.write to
    # raise — but the parent directory's File.mkdir_p would still
    # succeed; only the write_inbox_fallback path's `with` block would
    # fall into the {:error, reason} else branch if the append fails.
    # The cleanest forcing function is to set HOME to a path that
    # cannot be created (e.g. inside a non-directory file).
    test "inbox fallback returns {:error, :inbox_fallback_failed} when file append fails" do
      # Create a regular file at the path the inbox-fallback would
      # try to mkdir_p into. mkdir_p on an existing regular file
      # returns {:error, :eexist} (or similar).
      tmpdir = Path.join(System.tmp_dir!(), "gw_inbox_fail_#{System.unique_integer([:positive])}")
      blocker = Path.join(tmpdir, ".openclaw")
      File.mkdir_p!(tmpdir)
      File.write!(blocker, "not a directory")
      System.put_env("HOME", tmpdir)

      :meck.new(System, [:passthrough])
      :meck.expect(System, :cmd, fn "openclaw", _args, _env -> {"", 1} end)
      on_exit(fn ->
        :meck.unload()
        File.rm_rf!(tmpdir)
      end)

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:error, :inbox_fallback_failed} =
                   Client.send_telegram(%{"subject" => "fail", "from" => "x"})
        end)

      assert log =~ "Inbox fallback failed"
    end
  end

  # --- handle_connect/2 --------------------------------------------------

  describe "handle_connect/2" do
    test "returns :ok and transitions status to :waiting_challenge", %{state: state} do
      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_connect(%{}, state)
          assert new_state.status == :waiting_challenge
        end)

      assert log =~ "WS connected"
    end
  end

  # --- handle_frame/2 — text frames --------------------------------------

  describe "handle_frame/2 — connect.challenge" do
    setup do
      tmpdir = Path.join(System.tmp_dir!(), "gw_id_test_#{System.unique_integer([:positive])}")
      File.mkdir_p!(tmpdir)
      System.put_env("HOME", tmpdir)
      on_exit(fn -> File.rm_rf!(tmpdir) end)
      {:ok, tmpdir: tmpdir}
    end

    test "responds with a connect.req frame containing device auth", %{tmpdir: tmpdir, state: base} do
      nonce = "test-nonce-1234"
      ts = 1_700_000_000_000

      frame = {:text, Jason.encode!(%{
        "type" => "event",
        "event" => "connect.challenge",
        "payload" => %{"nonce" => nonce, "ts" => ts}
      })}

      state = %{base | status: :waiting_challenge}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:reply, {:text, reply_raw}, state} = Client.handle_frame(frame, state)
          assert state.status == :waiting_challenge
          assert state.req_id == 2

          assert {:ok, decoded} = Jason.decode(reply_raw)
          assert decoded["type"] == "req"
          assert decoded["method"] == "connect"
          assert decoded["params"]["device"]["nonce"] == nonce
          assert decoded["params"]["device"]["signature"] != nil
          assert decoded["params"]["device"]["publicKey"] != nil
        end)

      iamq_path = Path.join([tmpdir, ".openclaw", "iamq-device-identity.json"])
      assert File.exists?(iamq_path)
      assert log =~ "Sending connect.req with device auth"
    end
  end

  describe "handle_frame/2 — res ok (hello-ok)" do
    test "transitions to :authenticated and replies with a gateway.send frame", %{state: base} do
      state = %{base | status: :waiting_challenge, req_id: 5}

      frame = {:text, Jason.encode!(%{
        "type" => "res",
        "id" => "5",
        "ok" => true,
        "payload" => %{"type" => "hello-ok", "protocol" => 3}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:reply, {:text, reply_raw}, state} = Client.handle_frame(frame, state)
          assert state.status == :authenticated
          assert state.req_id == 6

          assert {:ok, decoded} = Jason.decode(reply_raw)
          assert decoded["type"] == "req"
          assert decoded["method"] == "gateway.send"
          assert decoded["params"]["account"] == "oc_gr_mq_bot"
          assert decoded["params"]["channel"] == "telegram"
          assert decoded["params"]["content"] == "hello"
        end)

      assert log =~ "Auth successful"
    end
  end

  describe "handle_frame/2 — res ok (after hello-ok, final send response)" do
    test "reaches the unexpected auth response path and closes with error", %{state: base} do
      state = %{base | status: :authenticated, req_id: 5}

      frame = {:text, Jason.encode!(%{
        "type" => "res",
        "id" => "6",
        "ok" => true,
        "payload" => %{"delivered" => true, "message_id" => "tg-1"}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          # After :authenticated state, a non-hello-ok res payload
          # falls into the catch-all `handle_auth_response/3` clause,
          # which logs a warning and closes the socket.
          assert {:close, new_state} = Client.handle_frame(frame, state)
          assert new_state.status == :closing
        end)

      assert log =~ "Unexpected auth response"
      assert_received {:gateway_result, {:error, "unexpected auth response"}}
    end
  end

  describe "handle_frame/2 — res ok=false (gateway error)" do
    test "sends :gateway_result {:error, payload} to caller and closes", %{state: state} do
      frame = {:text, Jason.encode!(%{
        "type" => "res",
        "id" => "5",
        "ok" => false,
        "payload" => %{"error" => "rate_limited"}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:close, new_state} = Client.handle_frame(frame, state)
          assert new_state.status == :closing
        end)

      assert_received {:gateway_result, {:error, %{"error" => "rate_limited"}}}
      assert log =~ "Gateway returned error"
    end
  end

  describe "handle_frame/2 — unexpected event" do
    test "logs the event and returns :ok with state unchanged", %{state: state} do
      frame = {:text, ~s({"event":"something_unexpected"})}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_frame(frame, state)
          assert new_state == state
        end)

      assert log =~ "Unexpected event"
    end
  end

  describe "handle_frame/2 — unknown JSON shape" do
    test "logs warning and returns :ok with state unchanged", %{state: state} do
      frame = {:text, ~s({"hello":"world"})}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_frame(frame, state)
          assert new_state == state
        end)

      assert log =~ "Unexpected frame"
    end
  end

  describe "handle_frame/2 — non-text frame" do
    test "binary frame logs warning and returns :ok with state unchanged", %{state: state} do
      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_frame({:binary, <<1, 2, 3>>}, state)
          assert new_state == state
        end)

      assert log =~ "Unexpected frame type"
    end
  end

  describe "handle_frame/2 — invalid JSON" do
    test "logs warning and returns :ok with state unchanged (no rescue fires)", %{state: state} do
      # Jason.decode returns {:error, _} for invalid JSON — it does NOT
      # raise, so the rescue branch is never entered. The frame is
      # treated as the catch-all `other ->` case and silently dropped.
      frame = {:text, "{not valid json"}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_frame(frame, state)
          assert new_state == state
        end)

      assert log =~ "Unexpected frame"
    end
  end

  # --- handle_disconnect/2 -----------------------------------------------

  describe "handle_disconnect/2" do
    test "sends :gateway_result {:error, reason} to caller and returns :done", %{state: state} do
      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:ok, new_state} = Client.handle_disconnect({:remote, :closed}, state)
          assert new_state.status == :done
        end)

      assert_received {:gateway_result, {:error, msg}}
      assert msg =~ "disconnected"
      assert log =~ "WS disconnected"
    end
  end

  # --- start_link/4 — env-var wiring only (mocked transport) -------------

  describe "start_link/4" do
    test "assembles state with caller, req_id=1, status=:idle" do
      :meck.new(WebSockex, [:passthrough])
      :meck.expect(WebSockex, :start_link, fn _url, _mod, _state, _opts ->
        {:ok, spawn(fn -> :ok end)}
      end)
      on_exit(fn -> :meck.unload() end)

      caller = self()
      assert {:ok, _pid} = Client.start_link({"ws://x", "tok", %{a: 1}, caller})

      assert :meck.called(WebSockex, :start_link, [
               "ws://x",
               Client,
               :_,
               [name: Client]
             ])

      # :meck.history/1 returns 3-tuples {pid, {module, fun, args}, result}
      [{_pid, {_mod, _fun, args}, _result}] = :meck.history(WebSockex)
      [_url, _mod, state, _opts] = args
      assert state.req_id == 1
      assert state.status == :idle
      assert state.caller == caller
      assert state.token == "tok"
    end
  end

  # --- try_ws_rpc success path -------------------------------------------
  #
  # The :ok branch in try_ws_rpc is reached when start_link_sync returns
  # :ok. start_link_sync returns the result of the spawned monitor's
  # :gateway_result message — so we need a mock WebSockex pid that
  # sends `{:gateway_result, :ok}` to the spawned monitor process.
  # This is the only test path that hits L37 (Telegram delivery via WS
  # RPC log line) and L61 (the `{:ok, _pid} -> :ok` branch in
  # try_ws_rpc).

  describe "send_telegram/1 — WS RPC success" do
    test "logs 'Telegram delivery via WS RPC' when start_link_sync returns {:ok, _pid}" do
      :meck.new(WebSockex, [:passthrough])
      :meck.expect(WebSockex, :start_link, fn _url, _mod, _state, _opts ->
        # The monitor fn (in start_link_sync) is the current process at
        # the time start_link is called — capture it and have a child
        # pid deliver `{:gateway_result, {:ok, :fake_pid}}`. The monitor
        # forwards the tuple verbatim, so start_link_sync returns
        # `{:ok, :fake_pid}`, which matches the `{:ok, _pid} -> :ok`
        # branch in try_ws_rpc (L61).
        parent = self()
        pid = spawn(fn -> send(parent, {:gateway_result, {:ok, :fake_pid}}) end)
        {:ok, pid}
      end)
      on_exit(fn -> :meck.unload() end)

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert :ok = Client.send_telegram(%{"subject" => "x", "from" => "y"})
        end)

      assert log =~ "Telegram delivery via WS RPC"
    end
  end

  # --- format_message variations -----------------------------------------
  #
  # format_message/1 is private. We exercise it indirectly by calling
  # send_telegram with various message shapes and capturing the
  # delivery_payload that the WebSockex mock observes. The mock stores
  # the state argument passed to start_link/4; the state contains
  # delivery_payload, which was formatted before being handed to the WS
  # RPC layer.

  describe "send_telegram/1 — format_message variations" do
    setup do
      test_pid = self()
      :meck.new(WebSockex, [:passthrough])
      :meck.expect(WebSockex, :start_link, fn _url, _mod, state, _opts ->
        send(test_pid, {:captured_state, state})
        {:ok, spawn(fn -> :ok end)}
      end)
      on_exit(fn -> :meck.unload() end)
      :ok
    end

    test "non-map message falls through to the catch-all '[IAMQ] New message received'" do
      Task.start(fn -> Client.send_telegram("not-a-map") end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      assert content == "[IAMQ] New message received"
    end

    test "map with no body, no subject uses defaults" do
      Task.start(fn -> Client.send_telegram(%{"from" => "alice"}) end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      assert content == "[IAMQ] alice: "
    end

    test "map with body and empty body is formatted as 'from: subject' only" do
      Task.start(fn -> Client.send_telegram(%{"from" => "alice", "subject" => "hello"}) end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      # No body key, so the `else` branch fires (L484)
      assert content == "[IAMQ] alice: hello"
    end

    test "map with empty body string still includes 'from: subject'" do
      Task.start(fn ->
        Client.send_telegram(%{"from" => "alice", "subject" => "hello", "body" => ""})
      end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      # body == "" so the `if body != ""` guard excludes the body line
      assert content == "[IAMQ] alice: hello"
    end

    test "map with non-empty body appends 'from: subject\\nbody'" do
      Task.start(fn ->
        Client.send_telegram(%{"from" => "alice", "subject" => "hello", "body" => "world"})
      end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      assert content == "[IAMQ] alice: hello\nworld"
    end

    test "map with body containing valid JSON but non-deliver_report action falls through to default formatting" do
      body = Jason.encode!(%{"action" => "other", "data" => "x"})

      Task.start(fn ->
        Client.send_telegram(%{"from" => "alice", "subject" => "hello", "body" => body})
      end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      # body_json["action"] != "deliver_report", so the else branch
      # (L478) fires.
      assert content == "[IAMQ] alice: hello\n" <> body
    end

    test "map with body containing deliver_report action formats as weekly report" do
      body =
        Jason.encode!(%{
          "action" => "deliver_report",
          "report" => %{"filename" => "weekly.md", "content" => "## Summary\nAll green."}
        })

      Task.start(fn ->
        Client.send_telegram(%{"from" => "gitrepo", "subject" => "weekly", "body" => body})
      end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      assert content =~ "[GitRepo] Weekly Report from gitrepo"
      assert content =~ "weekly.md"
      assert content =~ "All green."
    end

    test "map with body containing invalid JSON falls through rescue to default formatting" do
      # handle_frame/2's case clause is not involved here — we go
      # straight through send_telegram -> format_message. Jason.decode!
      # raises, the rescue branch (L480-482) fires, default formatting.
      Task.start(fn ->
        Client.send_telegram(%{
          "from" => "alice",
          "subject" => "hello",
          "body" => "{not valid json"
        })
      end)
      assert_receive {:captured_state, %{delivery_payload: %{content: content}}}, 2_000
      assert content == "[IAMQ] alice: hello\n{not valid json"
    end
  end

  # --- load_iamq_device_identity with pre-populated file ----------------
  #
  # load_or_generate_identity takes the IAMQ path branch when the file
  # already exists. We pre-write a valid identity JSON with a real
  # Ed25519 keypair (32-byte keys) and assert that the handle_challenge
  # path uses it rather than generating a fresh one. This exercises
  # load_iamq_device_identity's with-block happy path (L420-434).

  describe "handle_frame/2 — pre-populated IAMQ identity" do
    setup do
      tmpdir = Path.join(System.tmp_dir!(), "gw_pre_id_#{System.unique_integer([:positive])}")
      File.mkdir_p!(Path.join([tmpdir, ".openclaw"]))

      # Real Ed25519 keypair — handle_challenge uses :crypto.sign which
      # requires 32-byte keys.
      {pub_raw, priv_raw} = :crypto.generate_key(:eddsa, :ed25519)

      iamq_path = Path.join([tmpdir, ".openclaw", "iamq-device-identity.json"])
      File.write!(iamq_path, Jason.encode!(%{
        "device_id" => "preset-device-id",
        "public_key" => Base.url_encode64(pub_raw, padding: false),
        "private_key" => Base.url_encode64(priv_raw, padding: false)
      }))
      System.put_env("HOME", tmpdir)
      on_exit(fn -> File.rm_rf!(tmpdir) end)
      {:ok, tmpdir: tmpdir}
    end

    test "loads the pre-populated identity (not generating a new one)", %{state: base} do
      state = %{base | status: :waiting_challenge}
      frame = {:text, Jason.encode!(%{
        "type" => "event",
        "event" => "connect.challenge",
        "payload" => %{"nonce" => "n", "ts" => 1_700_000_000_000}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:reply, {:text, reply_raw}, _state} = Client.handle_frame(frame, state)
          # Signature uses the pre-populated private_key bytes
          assert {:ok, %{"params" => %{"device" => device}}} = Jason.decode(reply_raw)
          assert device["id"] == "preset-device-id"
        end)

      assert log =~ "Loading IAMQ identity"
      assert log =~ "preset-device-id"
      refute log =~ "No IAMQ identity"
    end
  end

  # --- handle_challenge exception path ----------------------------------
  #
  # When build_device_auth_payload_v3 raises, handle_challenge's rescue
  # fires (L268-276), sending a :gateway_result error to the caller and
  # closing the connection. We force the exception by mocking
  # :crypto.sign to raise — :crypto.sign is called inside
  # handle_challenge with a valid key/nonce, so a mock that raises
  # trips the rescue without changing the public API surface.

  describe "handle_frame/2 — challenge handler exception" do
    setup do
      tmpdir = Path.join(System.tmp_dir!(), "gw_exc_#{System.unique_integer([:positive])}")
      File.mkdir_p!(Path.join([tmpdir, ".openclaw"]))
      System.put_env("HOME", tmpdir)
      on_exit(fn -> File.rm_rf!(tmpdir) end)
      :meck.new(:crypto, [:passthrough])
      on_exit(fn -> :meck.unload() end)
      :ok
    end

    test "rescue branch closes the connection and reports error to caller", %{state: base} do
      # Force :crypto.sign to raise — any arity is fine because the
      # meck default catches all calls.
      :meck.expect(:crypto, :sign, fn _, _, _, _ -> raise "forced crypto failure" end)

      state = %{base | status: :waiting_challenge}
      frame = {:text, Jason.encode!(%{
        "type" => "event",
        "event" => "connect.challenge",
        "payload" => %{"nonce" => "n", "ts" => 1_700_000_000_000}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:close, new_state} = Client.handle_frame(frame, state)
          assert new_state.status == :closing
        end)

      assert log =~ "handle_challenge exception"
      assert_received {:gateway_result, {:error, msg}}
      assert msg =~ "challenge handler exception"
    end
  end

  # --- handle_frame rescue branch (L193-196) ----------------------------
  #
  # The rescue in handle_frame fires when any expression in the case
  # body raises. The simplest way to trigger it is to mock
  # Logger.error/1 to raise — that way the line that *would* be hit in
  # the rescue (Logger.error) itself is what makes the rescue fire.
  # In practice that's a self-reference; a cleaner path is to have a
  # payload that triggers Jason.encode! to fail.

  describe "handle_frame/2 — exception in case body" do
    test "rescue closes connection and reports error to caller", %{state: base} do
      # A challenge payload that is JSON-decodable but has no "nonce"
      # key will fail the pattern match on `%{"nonce" => nonce, "ts" => _}`
      # with a MatchError. MatchError IS raised in the case body, so
      # the rescue at L192-196 catches it.
      frame = {:text, Jason.encode!(%{
        "type" => "event",
        "event" => "connect.challenge",
        "payload" => %{"other" => "no nonce here"}
      })}

      log =
        ExUnit.CaptureLog.capture_log(fn ->
          assert {:close, new_state} = Client.handle_frame(frame, base)
          assert new_state.status == :closing
        end)

      assert log =~ "Exception in handle_frame"
      assert_received {:gateway_result, {:error, msg}}
      assert msg =~ "frame handler exception"
    end
  end
end
