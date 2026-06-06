defmodule IamqSidecar.MqClientTest do
  use ExUnit.Case, async: false

  @moduletag :smoke

  # --- Test adapter ------------------------------------------------------
  #
  # The MQ client does outbound HTTP via Req, which delegates to Finch
  # by default. We override :adapter with a function that returns a
  # canned Req.Response for the path being requested. The adapter is
  # wired in by setting :iamq_sidecar's :req_options app env, which
  # the client already consults in extra_req_opts/0 (used by the cron
  # HTTP helpers req_get/req_post/req_patch/req_delete).
  #
  # Note: the GenServer init/handle_call paths use do_get/do_register/
  # do_heartbeat directly, which do NOT consult extra_req_opts. Those
  # paths require a real IAMQ endpoint (or a Bypass server) and are
  # exercised manually in dev — see WAVE2 follow-up issue.

  defp stub_adapter do
    fn request ->
      body =
        case {request.method, request.url.path} do
          {:get, "/agents"} -> []
          {:get, "/status"} -> %{"status" => "ok"}
          {:get, "/crons"} -> []
          {:get, "/crons/cron-1"} -> %{"id" => "cron-1", "expression" => "*/5 * * * *"}
          {:post, "/crons"} -> %{"id" => "cron-1", "expression" => "*/5 * * * *"}
          {:patch, "/crons/cron-1"} -> %{"id" => "cron-1", "enabled" => false}
          _ -> %{"ok" => true}
        end

      response =
        Req.Response.new(
          status: 200,
          body: body,
          headers: %{"content-type" => "application/json"}
        )

      {request, response}
    end
  end

  defp failing_adapter do
    fn request ->
      response =
        Req.Response.new(
          status: 500,
          body: %{"error" => "simulated outage"},
          headers: %{"content-type" => "application/json"}
        )

      {request, response}
    end
  end

  setup do
    previous = Application.get_env(:iamq_sidecar, :req_options, [])

    on_exit(fn ->
      Application.put_env(:iamq_sidecar, :req_options, previous)
    end)

    :ok
  end

  # --- list_crons/1 -----------------------------------------------------
  #
  # The architect's spec for this smoke test: a "no crons registered"
  # response from IAMQ is {:ok, []} — exactly the case the architect
  # flagged as gate-theater (a gate that was bypassed because no test
  # existed). With this test, a regression in list_crons/1's success
  # path will fail the suite.

  describe "list_crons/1" do
    test "returns {:ok, []} when IAMQ reports an empty list" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: stub_adapter())

      assert {:ok, []} = IamqSidecar.MqClient.list_crons(agent_id: "test-agent")
    end

    test "returns {:error, _} when IAMQ returns a non-2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: failing_adapter())

      assert {:error, message} = IamqSidecar.MqClient.list_crons(agent_id: "test-agent")
      assert message =~ "HTTP 500"
    end
  end

  # --- register_cron/3 --------------------------------------------------

  describe "register_cron/3" do
    test "returns {:ok, body} on 2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: stub_adapter())

      assert {:ok, %{"id" => "cron-1"}} =
               IamqSidecar.MqClient.register_cron("test", "*/5 * * * *", agent_id: "test-agent")
    end

    test "returns {:error, _} on non-2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: failing_adapter())

      assert {:error, message} =
               IamqSidecar.MqClient.register_cron("test", "*/5 * * * *", agent_id: "test-agent")

      assert message =~ "HTTP 500"
    end
  end

  # --- get_cron/1 -------------------------------------------------------

  describe "get_cron/1" do
    test "returns {:ok, cron_map} on 2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: stub_adapter())

      assert {:ok, %{"id" => "cron-1"}} = IamqSidecar.MqClient.get_cron("cron-1")
    end

    test "returns {:error, _} on non-2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: failing_adapter())

      assert {:error, message} = IamqSidecar.MqClient.get_cron("cron-1")
      assert message =~ "HTTP 500"
    end
  end

  # --- update_cron/2 ----------------------------------------------------

  describe "update_cron/2" do
    test "returns {:ok, body} on 2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: stub_adapter())

      assert {:ok, %{"id" => "cron-1", "enabled" => false}} =
               IamqSidecar.MqClient.update_cron("cron-1", %{enabled: false})
    end

    test "returns {:error, _} on non-2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: failing_adapter())

      assert {:error, message} = IamqSidecar.MqClient.update_cron("cron-1", %{})
      assert message =~ "HTTP 500"
    end
  end

  # --- delete_cron/1 ----------------------------------------------------

  describe "delete_cron/1" do
    test "returns :ok on 2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: stub_adapter())

      assert :ok = IamqSidecar.MqClient.delete_cron("cron-1")
    end

    test "returns {:error, _} on non-2xx" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: failing_adapter())

      assert {:error, message} = IamqSidecar.MqClient.delete_cron("cron-1")
      assert message =~ "HTTP 500"
    end
  end
end
