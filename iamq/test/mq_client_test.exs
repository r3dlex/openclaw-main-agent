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

  # Adapter that returns a /crons body that is NOT a list — exercises the
  # L83 catch-all branch in list_crons/1 (`{:ok, %{status: 200, body: b}} -> {:ok, b}`
  # when `is_list(b)` is false).
  defp nonlist_crons_adapter do
    fn request ->
      body =
        case {request.method, request.url.path} do
          {:get, "/crons"} -> %{"data" => "not-a-list"}
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

    test "returns {:ok, body} when 200 body is non-list (covers L83 catch-all)" do
      Application.put_env(:iamq_sidecar, :req_options, adapter: nonlist_crons_adapter())

      # L83 fires when 200 body is a non-list map — the catch-all
      # `{:ok, %{status: 200, body: b}} -> {:ok, b}` branch returns the
      # body as-is rather than wrapping it.
      assert {:ok, %{"data" => "not-a-list"}} =
               IamqSidecar.MqClient.list_crons(agent_id: "test-agent")
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

  # --- network-error (Req {:error, _} clause) ---------------------------
  #
  # Each cron helper has a `{:error, reason} -> {:error, reason}` clause
  # that fires when Req returns `{:error, _}` (e.g. connection refused,
  # DNS failure). The cron helpers are simple non-GenServer functions
  # that go straight to Req, so we mock Req at the module boundary with
  # :meck — same pattern as the GenServer test suite. This exercises
  # the `{:error, reason} -> {:error, reason}` clauses in:
  #   L65  register_cron/3
  #   L85  list_crons/1
  #   L100 get_cron/1
  #   L115 update_cron/2
  #   L130 delete_cron/1

  describe "cron helpers — Req {:error, _} clauses" do
    setup do
      # Point IAMQ_HTTP_URL at an unroutable port so Req returns
      # `{:error, _}` for every call — exercises the
      # `{:error, reason} -> {:error, reason}` clauses in each cron
      # helper (L65, L85, L100, L115, L130). Port 1 on localhost is
      # reserved and refuses connections immediately. retry: false
      # cuts the test from ~15s (3 retries × 5s timeout) to <1s.
      previous_url = System.get_env("IAMQ_HTTP_URL")
      System.put_env("IAMQ_HTTP_URL", "http://127.0.0.1:1")
      Application.put_env(:iamq_sidecar, :req_options, retry: false)
      on_exit(fn ->
        if previous_url,
          do: System.put_env("IAMQ_HTTP_URL", previous_url),
          else: System.delete_env("IAMQ_HTTP_URL")
      end)
      :ok
    end

    test "register_cron returns {:error, _} when HTTP request fails (covers L65)" do
      assert {:error, _} =
               IamqSidecar.MqClient.register_cron("t", "*/5 * * * *", agent_id: "a")
    end

    test "list_crons returns {:error, _} when HTTP request fails (covers L85)" do
      assert {:error, _} = IamqSidecar.MqClient.list_crons(agent_id: "a")
    end

    test "get_cron returns {:error, _} when HTTP request fails (covers L100)" do
      assert {:error, _} = IamqSidecar.MqClient.get_cron("cron-1")
    end

    test "update_cron returns {:error, _} when HTTP request fails (covers L115)" do
      assert {:error, _} = IamqSidecar.MqClient.update_cron("cron-1", %{})
    end

    test "delete_cron returns {:error, _} when HTTP request fails (covers L130)" do
      assert {:error, _} = IamqSidecar.MqClient.delete_cron("cron-1")
    end
  end

end

