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
end
