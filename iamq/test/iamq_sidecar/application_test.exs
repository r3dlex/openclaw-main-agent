defmodule IamqSidecar.ApplicationTest do
  @moduledoc """
  Tests for `IamqSidecar.Application` — verifies the supervisor's
  children and strategy without standing up real WS / HTTP transports.

  Approach: the children's `start_link/1` callbacks are mocked to
  return `:ignore`, so the supervisor starts up but no real work
  happens. The test process traps exits so the supervisor's
  brutal_kill shutdown doesn't propagate up. Cleanup is done in-test
  (rather than in on_exit) because the brutal_kill can race with
  meck's process teardown.
  """
  use ExUnit.Case, async: false

  defp safe_unload(mod) do
    try do
      :meck.unload(mod)
    rescue
      _ -> :ok
    end
  end

  defp start_and_cleanup do
    :meck.new(IamqSidecar.MqClient, [:passthrough])
    :meck.expect(IamqSidecar.MqClient, :start_link, fn _opts -> :ignore end)
    :meck.new(IamqSidecar.MqWsClient, [:passthrough])
    :meck.expect(IamqSidecar.MqWsClient, :start_link, fn _opts -> :ignore end)

    Process.flag(:trap_exit, true)

    # Make sure no leftover supervisor is registered from a previous run.
    case Process.whereis(IamqSidecar.Supervisor) do
      nil -> :ok
      pid -> Process.exit(pid, :kill)
    end
  end

  defp stop_supervisor(sup_pid) do
    ref = Process.monitor(sup_pid)
    Supervisor.stop(sup_pid, :brutal_kill)
    assert_receive {:DOWN, ^ref, :process, ^sup_pid, _}, 1_000

    safe_unload(IamqSidecar.MqClient)
    safe_unload(IamqSidecar.MqWsClient)
  end

  test "Application.start/2 returns a supervisor pid" do
    start_and_cleanup()

    assert {:ok, sup_pid} = IamqSidecar.Application.start(:normal, [])
    assert is_pid(sup_pid)
    assert Process.alive?(sup_pid)

    stop_supervisor(sup_pid)
  end

  test "supervisor registers under IamqSidecar.Supervisor" do
    start_and_cleanup()

    {:ok, sup_pid} = IamqSidecar.Application.start(:normal, [])
    assert Process.whereis(IamqSidecar.Supervisor) == sup_pid

    stop_supervisor(sup_pid)
  end

  test "supervisor uses one_for_one strategy" do
    start_and_cleanup()

    {:ok, sup_pid} = IamqSidecar.Application.start(:normal, [])

    # The supervisor's state tuple is `{:state, name, strategy, ...}` —
    # extract the strategy element directly.
    state = :sys.get_state(sup_pid)
    assert elem(state, 2) == :one_for_one

    stop_supervisor(sup_pid)
  end
end
