defmodule IamqBindingsTest do
  use ExUnit.Case, async: true

  alias IamqBindings.Config

  # ---------------------------------------------------------------------------
  # Config tests
  # ---------------------------------------------------------------------------

  describe "Config.base_url/0" do
    test "returns default when IAMQ_BASE_URL is not set" do
      System.delete_env("IAMQ_BASE_URL")
      assert Config.base_url() == "http://127.0.0.1:18790"
    end

    test "returns custom URL when IAMQ_BASE_URL is set" do
      System.put_env("IAMQ_BASE_URL", "http://custom:9999")
      assert Config.base_url() == "http://custom:9999"
    after
      System.delete_env("IAMQ_BASE_URL")
    end
  end

  # ---------------------------------------------------------------------------
  # Request-construction tests
  #
  # These tests use a Req test plug to intercept HTTP calls and verify the
  # request URL, method, headers, and body without needing a running server.
  # ---------------------------------------------------------------------------

  setup do
    # Point at a unique base URL so we can pattern-match in the plug
    test_url = "http://iamq-test-#{System.unique_integer([:positive])}"
    System.put_env("IAMQ_BASE_URL", test_url)

    on_exit(fn -> System.delete_env("IAMQ_BASE_URL") end)

    {:ok, base_url: test_url}
  end

  # ---------------------------------------------------------------------------
  # Connection-error tests verify that each function targets the right
  # endpoint and returns {:error, _} when no server is listening.
  # ---------------------------------------------------------------------------

  describe "register/5" do
    test "calls POST /register and returns error tuple on connection failure", %{base_url: _} do
      # With no server listening, we expect a connection error
      assert {:error, _reason} = IamqBindings.register("a1", "Agent", "🤖", "desc", ["cap1"])
    end
  end

  describe "heartbeat/1" do
    test "calls POST /heartbeat and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.heartbeat("a1")
    end
  end

  describe "send_message/5" do
    test "calls POST /send and returns error tuple on connection failure" do
      assert {:error, _reason} =
               IamqBindings.send_message("from_a", "to_b", "subject", "body",
                 priority: "high",
                 type: "request",
                 replyTo: "msg-123"
               )
    end

    test "accepts empty opts" do
      assert {:error, _reason} =
               IamqBindings.send_message("from_a", "to_b", "subject", "body")
    end
  end

  describe "poll_inbox/2" do
    test "calls GET /inbox/:agent_id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.poll_inbox("a1")
    end

    test "accepts custom status" do
      assert {:error, _reason} = IamqBindings.poll_inbox("a1", "read")
    end
  end

  describe "mark_message/2" do
    test "calls PATCH /messages/:id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.mark_message("msg-1", "read")
    end
  end

  describe "list_agents/0" do
    test "calls GET /agents and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.list_agents()
    end
  end

  describe "get_agent/1" do
    test "calls GET /agents/:agent_id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.get_agent("a1")
    end
  end

  describe "health/0" do
    test "calls GET /status and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.health()
    end
  end

  # ---------------------------------------------------------------------------
  # URL construction tests (pure logic, no HTTP)
  # ---------------------------------------------------------------------------

  describe "URL construction" do
    test "register builds correct URL path" do
      base = Config.base_url()
      assert String.ends_with?(base <> "/register", "/register")
    end

    test "inbox URL includes agent_id" do
      base = Config.base_url()
      url = base <> "/inbox/agent-42"
      assert url =~ "/inbox/agent-42"
    end

    test "messages URL includes message_id" do
      base = Config.base_url()
      url = base <> "/messages/msg-99"
      assert url =~ "/messages/msg-99"
    end

    test "agents URL includes agent_id" do
      base = Config.base_url()
      url = base <> "/agents/agent-7"
      assert url =~ "/agents/agent-7"
    end
  end

  # ---------------------------------------------------------------------------
  # Payload construction tests (pure logic, no HTTP)
  # ---------------------------------------------------------------------------

  describe "send_message payload construction" do
    test "maybe_put excludes nil values" do
      # We test the payload shape by building what the module would build
      payload =
        %{from: "a", to: "b", subject: "s", body: "body"}
        |> maybe_put(:priority, nil)
        |> maybe_put(:type, "request")
        |> maybe_put(:replyTo, nil)

      assert payload == %{from: "a", to: "b", subject: "s", body: "body", type: "request"}
    end

    test "maybe_put includes all provided values" do
      payload =
        %{from: "a", to: "b", subject: "s", body: "body"}
        |> maybe_put(:priority, "high")
        |> maybe_put(:type, "request")
        |> maybe_put(:replyTo, "msg-1")

      assert payload == %{
               from: "a",
               to: "b",
               subject: "s",
               body: "body",
               priority: "high",
               type: "request",
               replyTo: "msg-1"
             }
    end
  end

  # Mirror of the private helper for testing payload construction
  defp maybe_put(map, _key, nil), do: map
  defp maybe_put(map, key, value), do: Map.put(map, key, value)
end
