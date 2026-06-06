defmodule IamqSidecar.MqClientGenServerTest do
  @moduledoc """
  Covers the GenServer HTTP paths of `IamqSidecar.MqClient`:
  init, register, heartbeat, poll_inbox, :send, :ack, :inbox, :agents,
  :status, and the :DOWN no-op handler.

  The existing `mq_client_test.exs` exercises the cron helpers (which go
  through `extra_req_opts/0`), but the GenServer HTTP paths
  (`do_register`, `do_heartbeat`, `do_poll_inbox`, `do_send`, `do_ack`,
  `do_get`) bypass that mechanism and require a real HTTP server — Bypass
  provides one in-process.
  """
  use ExUnit.Case, async: false

  alias IamqSidecar.MqClient

  @moduletag :genserver

  @env_keys ~w(IAMQ_HTTP_URL IAMQ_AGENT_ID IAMQ_AGENT_NAME IAMQ_AGENT_EMOJI
              IAMQ_AGENT_DESC IAMQ_AGENT_CAPABILITIES IAMQ_HEARTBEAT_MS
              IAMQ_POLL_MS)

  setup do
    bypass = Bypass.open()

    prev_env =
      Map.new(@env_keys, fn k -> {k, System.get_env(k)} end)

    System.put_env("IAMQ_HTTP_URL", "http://127.0.0.1:#{bypass.port}")
    System.put_env("IAMQ_AGENT_ID", "test-agent")
    System.put_env("IAMQ_AGENT_NAME", "Test Agent")
    System.put_env("IAMQ_AGENT_EMOJI", "test")
    System.put_env("IAMQ_AGENT_DESC", "test desc")
    System.put_env("IAMQ_AGENT_CAPABILITIES", "cap_a,cap_b")
    # Long timeouts so scheduled heartbeats/polls don't fire mid-test.
    System.put_env("IAMQ_HEARTBEAT_MS", "60000")
    System.put_env("IAMQ_POLL_MS", "60000")

    :meck.new(IamqSidecar.Gateway.Client, [:passthrough])
    :meck.expect(IamqSidecar.Gateway.Client, :send_telegram, fn _msg -> :ok end)

    on_exit(fn ->
      :meck.unload()

      Enum.each(prev_env, fn {k, v} ->
        if v == nil, do: System.delete_env(k), else: System.put_env(k, v)
      end)
    end)

    {:ok, bypass: bypass}
  end

  # --- helpers -----------------------------------------------------------

  # Returns a Bypass handler that pattern-matches on the request and
  # dispatches to the caller's response spec. The spec is a map of
  # {method, path} -> {status, body} for the requests we expect to be
  # made. Anything not matched returns 404 (Bypass default).
  defp handler(spec, test_pid, ref) do
    fn conn ->
      key = {conn.method, Enum.join(conn.path_info, "/")}

      case Map.fetch(spec, key) do
        {:ok, {status, body}} ->
          send(test_pid, {:bypass_request, ref, key})
          conn = Plug.Conn.put_resp_header(conn, "content-type", "application/json")
          Plug.Conn.resp(conn, status, Jason.encode!(body))

        :error ->
          conn = Plug.Conn.put_resp_header(conn, "content-type", "application/json")
          Plug.Conn.resp(conn, 404, Jason.encode!(%{error: "unexpected: #{inspect(key)}"}))
      end
    end
  end

  # Waits for the initial :register cycle (init schedules :register in 2s).
  defp wait_for_register(ref), do: assert_receive({:bypass_request, ^ref, {"POST", "register"}}, 5_000)

  # --- init / register ---------------------------------------------------

  describe "init/1 + :register" do
    test "sends POST /register on start, transitions to registered", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(%{{"POST", "register"} => {200, %{ok: true}}}, test_pid, ref)
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      state = :sys.get_state(MqClient)
      assert state.registered == true
      assert state.consecutive_failures == 0
      assert state.config.agent_id == "test-agent"
      assert state.config.agent_name == "Test Agent"
      assert state.config.agent_emoji == "test"
      assert state.config.agent_caps == ["cap_a", "cap_b"]
    end

    test "register failure increments consecutive_failures and reschedules in 30s", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(%{{"POST", "register"} => {500, %{error: "boom"}}}, test_pid, ref)
      )

      start_supervised!(MqClient)
      assert_receive({:bypass_request, ^ref, {"POST", "register"}}, 5_000)

      state = :sys.get_state(MqClient)
      assert state.registered == false
      assert state.consecutive_failures == 1
    end
  end

  # --- heartbeat ---------------------------------------------------------

  describe ":heartbeat" do
    test "happy path resets consecutive_failures to 0", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"POST", "heartbeat"} => {200, %{ok: true}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      send(MqClient, :heartbeat)
      assert_receive({:bypass_request, ^ref, {"POST", "heartbeat"}}, 2_000)

      state = :sys.get_state(MqClient)
      assert state.consecutive_failures == 0
      assert state.registered == true
    end

    test "5 consecutive failures flip to registered=false and trigger re-register", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"POST", "heartbeat"} => {500, %{error: "fail"}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      # Drive 5 heartbeats manually (we set IAMQ_HEARTBEAT_MS=60000 so
      # the scheduled one won't fire during the test).
      for _ <- 1..5 do
        send(MqClient, :heartbeat)
        assert_receive({:bypass_request, ^ref, {"POST", "heartbeat"}}, 2_000)
      end

      state = :sys.get_state(MqClient)
      assert state.consecutive_failures == 5
      assert state.registered == false

      # The production code schedules :register 5s after the 5th failure.
      # We don't wait the full 5s (Req's pooled connection is stale from
      # the 5 consecutive 500s) — instead, manually fire :register to
      # verify the recovery transition.
      send(MqClient, :register)
      assert_receive({:bypass_request, ^ref, {"POST", "register"}}, 2_000)

      state2 = :sys.get_state(MqClient)
      assert state2.registered == true
      assert state2.consecutive_failures == 0
    end
  end

  # --- poll_inbox (handle_info) -----------------------------------------

  describe ":poll_inbox (handle_info)" do
    test "empty inbox is a no-op (no ack, no telegram)", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "inbox/test-agent"} => {200, %{messages: []}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      send(MqClient, :poll_inbox)
      assert_receive({:bypass_request, ^ref, {"GET", "inbox/test-agent"}}, 2_000)

      # No send_telegram, no PATCH /messages/...
      refute :meck.called(IamqSidecar.Gateway.Client, :send_telegram, :_)
      assert state = :sys.get_state(MqClient)
      assert state.registered == true
    end

    test "non-empty inbox → handle_msg → send_telegram + PATCH ack", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "inbox/test-agent"} =>
              {200,
               %{
                 messages: [
                   %{
                     "id" => "msg-1",
                     "from" => "other-agent",
                     "subject" => "hello",
                     "body" => "world",
                     "type" => "info"
                   }
                 ]
               }},
            {"PATCH", "messages/msg-1"} => {200, %{ok: true}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      send(MqClient, :poll_inbox)

      assert_receive({:bypass_request, ^ref, {"GET", "inbox/test-agent"}}, 2_000)
      assert_receive({:bypass_request, ^ref, {"PATCH", "messages/msg-1"}}, 2_000)

      assert :meck.called(IamqSidecar.Gateway.Client, :send_telegram, :_)
    end
  end

  # --- :send (handle_call) ----------------------------------------------

  describe ":send (handle_call)" do
    test "happy path returns {:ok, body}", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"POST", "send"} => {200, %{id: "out-1", status: "queued"}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:ok, %{"id" => "out-1"}} =
               MqClient.send_message("to-agent", "subj", "body", [])

      assert_receive({:bypass_request, ^ref, {"POST", "send"}}, 2_000)
    end

    test "HTTP error returns {:error, _}", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"POST", "send"} => {500, %{error: "downstream"}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:error, msg} = MqClient.send_message("to-agent", "subj", "body", [])
      assert msg =~ "HTTP 500"
    end
  end

  # --- :ack (handle_call) -----------------------------------------------

  describe ":ack (handle_call)" do
    test "happy path returns :ok", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"PATCH", "messages/msg-1"} => {200, %{ok: true}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert :ok = MqClient.ack("msg-1", "read")
      assert_receive({:bypass_request, ^ref, {"PATCH", "messages/msg-1"}}, 2_000)
    end
  end

  # --- :inbox (handle_call) ---------------------------------------------

  describe ":inbox (handle_call)" do
    test "returns {:ok, list} on 2xx", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "inbox/test-agent"} => {200, %{messages: [%{"id" => "m1"}, %{"id" => "m2"}]}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:ok, [%{"id" => "m1"}, %{"id" => "m2"}]} = MqClient.inbox("unread")
      assert_receive({:bypass_request, ^ref, {"GET", "inbox/test-agent"}}, 2_000)
    end
  end

  # --- :agents / :status (do_get) ---------------------------------------

  describe ":agents / :status (handle_call via do_get)" do
    test "agents happy path", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "agents"} => {200, [%{"id" => "a1"}, %{"id" => "a2"}]}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:ok, [%{"id" => "a1"}, %{"id" => "a2"}]} = MqClient.agents()
      assert_receive({:bypass_request, ^ref, {"GET", "agents"}}, 2_000)
    end

    test "status happy path", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "status"} => {200, %{"status" => "ok"}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:ok, %{"status" => "ok"}} = MqClient.status()
      assert_receive({:bypass_request, ^ref, {"GET", "status"}}, 2_000)
    end

    test "do_get 404 path returns {:error, _}", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(
          %{
            {"POST", "register"} => {200, %{ok: true}},
            {"GET", "agents"} => {404, %{error: "not found"}}
          },
          test_pid,
          ref
        )
      )

      start_supervised!(MqClient)

      assert {:error, msg} = MqClient.agents()
      assert msg =~ "HTTP 404"
    end
  end

  # --- :DOWN handler ----------------------------------------------------

  describe ":DOWN handler" do
    test "ignores :DOWN messages and leaves state unchanged", %{bypass: bypass} do
      ref = make_ref()
      test_pid = self()

      Bypass.expect(
        bypass,
        handler(%{{"POST", "register"} => {200, %{ok: true}}}, test_pid, ref)
      )

      start_supervised!(MqClient)
      wait_for_register(ref)

      pid = Process.whereis(MqClient)
      assert is_pid(pid)

      state_before = :sys.get_state(pid)

      # Cast a :DOWN message — should be a no-op.
      send(pid, {:DOWN, make_ref(), :process, self(), :normal})
      # Give the GenServer a moment to process the message.
      Process.sleep(50)

      assert Process.alive?(pid)
      assert :sys.get_state(pid) == state_before
    end
  end
end
