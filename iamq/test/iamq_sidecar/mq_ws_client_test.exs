defmodule IamqSidecar.MqWsClientTest do
  @moduledoc """
  Tests for `IamqSidecar.MqWsClient` (IAMQ WebSocket consumer).

  Most of the public surface area is `WebSockex` behaviour callbacks
  (`handle_connect/2`, `handle_frame/2`, `handle_info/2`,
  `handle_disconnect/2`). They are pure functions of state and message
  and can be exercised directly without standing up a real WebSocket
  transport.

  The one impure call inside the module is `handle_push/1`, which calls
  `IamqSidecar.Gateway.Client.send_telegram/1` and
  `WebSockex.send_frame(IamqSidecar.MqWsClient, ...)` to ack the
  message. We mock the gateway with `:meck` (already a project dep) and
  install a tiny GenServer stand-in under the `IamqSidecar.MqWsClient`
  name to absorb the `WebSockex.send_frame` call — same pattern as
  `Orchestrator.MqWsClientTest` in the workday agent.
  """
  use ExUnit.Case, async: false

  alias IamqSidecar.MqWsClient

  @moduletag :ws

  defmodule StubServer do
    @moduledoc """
    Minimal GenServer stand-in for WebSockex. Captures frames sent via
    `WebSockex.send_frame/2` (which uses `:gen.call/4` with the magic
    tag `:"$websockex_send"`). Used only by MqWsClientTest.
    """
    use GenServer

    def start_link(_),
      do: GenServer.start_link(__MODULE__, %{}, name: IamqSidecar.MqWsClient)

    def init(_), do: {:ok, %{frames: []}}
    def frames, do: GenServer.call(IamqSidecar.MqWsClient, :frames)
    def reset, do: GenServer.call(IamqSidecar.MqWsClient, :reset)

    def handle_call(:frames, _from, state), do: {:reply, state.frames, state}
    def handle_call(:reset, _from, _state), do: {:reply, :ok, %{frames: []}}
    def handle_call(_other, _from, state), do: {:reply, {:error, :unhandled}, state}

    # WebSockex.send_frame/3 uses :gen.call(client, :"$websockex_send", frame, timeout)
    # which delivers `{:"$websockex_send", from, frame}` to handle_info.
    # The reply must go through :gen.reply/2 (not GenServer.reply/2).
    def handle_info({:"$websockex_send", from, frame}, state) do
      :gen.reply(from, :ok)
      {:noreply, %{state | frames: [frame | state.frames]}}
    end

    def handle_info(_, state), do: {:noreply, state}
    def handle_cast(_, state), do: {:noreply, state}
  end

  @base_state %{
    agent_id: "test-agent",
    ws_url: "ws://127.0.0.1:18793/ws"
  }

  setup do
    kill_and_wait(MqWsClient)
    {:ok, _pid} = StubServer.start_link([])

    :meck.new(IamqSidecar.Gateway.Client, [:passthrough])
    :meck.expect(IamqSidecar.Gateway.Client, :send_telegram, fn _msg -> :ok end)

    on_exit(fn ->
      :meck.unload()
      kill_and_wait(MqWsClient)
    end)

    :ok
  end

  # Use Process.monitor + :DOWN (not Process.exit which is async) so the
  # next StubServer.start_link does not hit :already_started when tests
  # run back-to-back.
  defp kill_and_wait(name) do
    case Process.whereis(name) do
      nil ->
        :ok

      pid ->
        ref = Process.monitor(pid)
        Process.unlink(pid)
        Process.exit(pid, :kill)

        receive do
          {:DOWN, ^ref, :process, ^pid, _} -> :ok
        after
          1_000 -> :ok
        end
    end
  end

  # --- handle_connect/2 --------------------------------------------------

  describe "handle_connect/2" do
    test "returns ok and schedules :do_register" do
      assert {:ok, state} = MqWsClient.handle_connect(%{}, @base_state)
      assert state == @base_state
      assert_received :do_register
    end
  end

  # --- handle_frame/2 — text frames --------------------------------------

  describe "handle_frame/2 — registered event" do
    test "returns ok and leaves state unchanged" do
      frame = {:text, ~s({"event":"registered","agent_id":"test-agent"})}
      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state
    end

    test "logs the registered agent id" do
      frame = {:text, ~s({"event":"registered","agent_id":"agent-99"})}
      log = ExUnit.CaptureLog.capture_log(fn ->
        MqWsClient.handle_frame(frame, @base_state)
      end)

      assert log =~ "Registered as agent-99"
    end
  end

  describe "handle_frame/2 — heartbeat_ack event" do
    test "returns ok and leaves state unchanged" do
      frame = {:text, ~s({"event":"heartbeat_ack"})}
      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state
    end
  end

  describe "handle_frame/2 — sent event" do
    test "returns ok and leaves state unchanged" do
      frame = {:text, ~s({"event":"sent","id":"msg-1"})}
      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state
    end
  end

  describe "handle_frame/2 — error event" do
    test "returns ok and logs the reason" do
      frame = {:text, ~s({"event":"error","reason":"server overloaded"})}
      log = ExUnit.CaptureLog.capture_log(fn ->
        assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
        assert state == @base_state
      end)

      assert log =~ "server overloaded"
    end
  end

  describe "handle_frame/2 — new_message event" do
    test "dispatches to handle_push (calls send_telegram) and acks via WebSockex" do
      :ok = StubServer.reset()

      msg = %{
        "id" => "msg-123",
        "from" => "other-agent",
        "subject" => "hello",
        "type" => "info"
      }

      frame = {:text, Jason.encode!(%{event: "new_message", message: msg})}

      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state

      # handle_push called send_telegram
      assert :meck.called(IamqSidecar.Gateway.Client, :send_telegram, [msg])

      # handle_push ack'd the message via WebSockex.send_frame
      [{:text, ack_payload}] = StubServer.frames()
      assert {:ok, %{"action" => "ack", "id" => "msg-123"}} = Jason.decode(ack_payload)
    end

    test "missing id is handled gracefully (no ack frame sent)" do
      :ok = StubServer.reset()

      msg = %{"from" => "a", "subject" => "s", "type" => "info"}
      frame = {:text, Jason.encode!(%{event: "new_message", message: msg})}

      assert {:ok, _} = MqWsClient.handle_frame(frame, @base_state)
      assert :meck.called(IamqSidecar.Gateway.Client, :send_telegram, :_)
      assert StubServer.frames() == []
    end
  end

  describe "handle_frame/2 — unknown event" do
    test "returns ok and leaves state unchanged" do
      frame = {:text, ~s({"event":"something_new","data":"x"})}
      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state
    end
  end

  describe "handle_frame/2 — invalid JSON" do
    test "returns ok and does not raise" do
      frame = {:text, "{not valid json"}
      assert {:ok, state} = MqWsClient.handle_frame(frame, @base_state)
      assert state == @base_state
    end
  end

  describe "handle_frame/2 — non-text frame" do
    test "binary frame returns ok with state unchanged" do
      assert {:ok, state} = MqWsClient.handle_frame({:binary, <<1, 2, 3>>}, @base_state)
      assert state == @base_state
    end
  end

  # --- handle_info/2 -----------------------------------------------------

  describe "handle_info/2" do
    test ":do_register replies with a register frame and schedules heartbeat" do
      assert {:reply, {:text, frame}, state} =
               MqWsClient.handle_info(:do_register, @base_state)

      assert {:ok, %{"action" => "register", "agent_id" => "test-agent"}} =
               Jason.decode(frame)

      assert state == @base_state
    end

    test ":send_heartbeat replies with a heartbeat frame and reschedules" do
      assert {:reply, {:text, frame}, state} =
               MqWsClient.handle_info(:send_heartbeat, @base_state)

      assert {:ok, %{"action" => "heartbeat"}} = Jason.decode(frame)
      assert state == @base_state
    end

    test "unknown info message returns ok with state unchanged" do
      assert {:ok, state} = MqWsClient.handle_info(:something_else, @base_state)
      assert state == @base_state
    end
  end

  # --- handle_disconnect/2 -----------------------------------------------

  describe "handle_disconnect/2" do
    test "logs warning and returns reconnect tuple" do
      conn_status = %{reason: :closed}
      state = @base_state

      # handle_disconnect sleeps @reconnect_interval (15s) before
      # returning. Run it in a task and verify it eventually returns
      # {:reconnect, state} without hanging the suite.
      task = Task.async(fn -> MqWsClient.handle_disconnect(conn_status, state) end)

      result =
        case Task.yield(task, 16_000) do
          {:ok, value} -> value
          nil -> Task.shutdown(task)
        end

      assert match?({:reconnect, ^state}, result)
    end
  end

  # --- start_link/1 — env var wiring only (no real transport) -----------
  #
  # We avoid calling start_link/1 end-to-end because the WS client has
  # handle_initial_conn_failure: true and a 15 s reconnect interval —
  # a connection failure would create a long-lived process that loops
  # forever. Instead, we mock WebSockex.start_link to verify the env
  # var wiring and state assembly without standing up a transport.

  describe "start_link/1 (env var wiring)" do
    setup do
      prev_url = System.get_env("IAMQ_WS_URL")
      prev_id = System.get_env("IAMQ_AGENT_ID")

      System.put_env("IAMQ_WS_URL", "ws://127.0.0.1:19999/ws")
      System.put_env("IAMQ_AGENT_ID", "start-link-agent")

      :meck.new(WebSockex, [:passthrough])
      :meck.expect(WebSockex, :start_link, fn _url, _mod, _state, _opts -> {:ok, spawn(fn -> :ok end)} end)

      on_exit(fn ->
        :meck.unload()

        if prev_url,
          do: System.put_env("IAMQ_WS_URL", prev_url),
          else: System.delete_env("IAMQ_WS_URL")

        if prev_id,
          do: System.put_env("IAMQ_AGENT_ID", prev_id),
          else: System.delete_env("IAMQ_AGENT_ID")
      end)

      :ok
    end

    test "reads IAMQ_WS_URL and IAMQ_AGENT_ID and calls WebSockex.start_link" do
      assert {:ok, _pid} = MqWsClient.start_link([])

      # WebSockex.start_link was called with the right URL and name.
      assert :meck.called(WebSockex, :start_link, [
               "ws://127.0.0.1:19999/ws",
               MqWsClient,
               %{agent_id: "start-link-agent", ws_url: "ws://127.0.0.1:19999/ws"},
               [name: MqWsClient, handle_initial_conn_failure: true]
             ])
    end

    test "falls back to default URL when IAMQ_WS_URL is unset" do
      System.delete_env("IAMQ_WS_URL")

      assert {:ok, _pid} = MqWsClient.start_link([])

      assert :meck.called(
               WebSockex,
               :start_link,
               ["ws://127.0.0.1:18793/ws", MqWsClient, :_, :_]
             )
    end

    test "raises System.EnvError if IAMQ_AGENT_ID is missing" do
      System.delete_env("IAMQ_AGENT_ID")

      assert_raise System.EnvError, fn ->
        MqWsClient.start_link([])
      end
    end
  end
end
