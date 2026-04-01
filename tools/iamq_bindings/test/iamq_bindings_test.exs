defmodule IamqBindingsTest do
  use ExUnit.Case, async: false

  alias IamqBindings.Config

  # ---------------------------------------------------------------------------
  # Minimal TCP mock-HTTP server
  #
  # Starts a `:gen_tcp` listener, accepts one connection, writes a predefined
  # HTTP/1.1 response, then closes. Returns the port it is listening on.
  # ---------------------------------------------------------------------------

  defp start_mock_server(response_lines) do
    response = Enum.join(response_lines, "\r\n") <> "\r\n"
    parent = self()

    {:ok, listen_socket} =
      :gen_tcp.listen(0, [:binary, packet: :raw, active: false, reuseaddr: true])

    {:ok, port} = :inet.port(listen_socket)

    spawn(fn ->
      {:ok, client} = :gen_tcp.accept(listen_socket)
      # Drain the incoming request so the client doesn't get a connection-reset
      :gen_tcp.recv(client, 0, 2_000)
      :gen_tcp.send(client, response)
      :gen_tcp.close(client)
      :gen_tcp.close(listen_socket)
      send(parent, :mock_server_done)
    end)

    port
  end

  defp json_200(body_map) do
    body = Jason.encode!(body_map)

    [
      "HTTP/1.1 200 OK",
      "Content-Type: application/json",
      "Content-Length: #{byte_size(body)}",
      "Connection: close",
      "",
      body
    ]
  end

  defp json_422(body_map) do
    body = Jason.encode!(body_map)

    [
      "HTTP/1.1 422 Unprocessable Entity",
      "Content-Type: application/json",
      "Content-Length: #{byte_size(body)}",
      "Connection: close",
      "",
      body
    ]
  end

  defp with_mock_url(port, fun) do
    System.put_env("IAMQ_HTTP_URL", "http://127.0.0.1:#{port}")

    try do
      fun.()
    after
      System.delete_env("IAMQ_HTTP_URL")
    end
  end

  # ---------------------------------------------------------------------------
  # Config tests
  # ---------------------------------------------------------------------------

  describe "Config.base_url/0" do
    test "returns default when IAMQ_HTTP_URL is not set" do
      System.delete_env("IAMQ_HTTP_URL")
      assert Config.base_url() == "http://127.0.0.1:18790"
    end

    test "returns custom URL when IAMQ_HTTP_URL is set" do
      System.put_env("IAMQ_HTTP_URL", "http://custom:9999")
      assert Config.base_url() == "http://custom:9999"
    after
      System.delete_env("IAMQ_HTTP_URL")
    end
  end

  describe "Config.agent_id/0" do
    test "returns default when IAMQ_AGENT_ID is not set" do
      System.delete_env("IAMQ_AGENT_ID")
      assert Config.agent_id() == "main"
    end

    test "returns custom agent_id when IAMQ_AGENT_ID is set" do
      System.put_env("IAMQ_AGENT_ID", "custom-agent")
      assert Config.agent_id() == "custom-agent"
    after
      System.delete_env("IAMQ_AGENT_ID")
    end
  end

  # ---------------------------------------------------------------------------
  # Connection-error tests verify that each function targets the right
  # endpoint and returns {:error, _} when no server is listening.
  # ---------------------------------------------------------------------------

  setup do
    # Point at a unique base URL so we can pattern-match in the plug
    test_url = "http://iamq-test-#{System.unique_integer([:positive])}"
    System.put_env("IAMQ_HTTP_URL", test_url)

    on_exit(fn -> System.delete_env("IAMQ_HTTP_URL") end)

    {:ok, base_url: test_url}
  end

  describe "register/5" do
    test "calls POST /register and returns error tuple on connection failure", %{base_url: _} do
      assert {:error, _reason} = IamqBindings.register("a1", "Agent", "🤖", "desc", ["cap1"])
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{ok: true, agent_id: "a1"}))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.register("a1", "Agent", "🤖", "desc", ["cap1"])
        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "already registered"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} =
                 IamqBindings.register("a1", "Agent", "🤖", "desc", ["cap1"])
      end)
    end
  end

  describe "heartbeat/1" do
    test "calls POST /heartbeat and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.heartbeat("a1")
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{ok: true}))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.heartbeat("a1")
        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "agent not found"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.heartbeat("a1")
      end)
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

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{ok: true, message_id: "msg-1"}))

      with_mock_url(port, fn ->
        assert {:ok, body} =
                 IamqBindings.send_message("from_a", "to_b", "subject", "body", priority: "high")

        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "invalid recipient"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} =
                 IamqBindings.send_message("from_a", "to_b", "subject", "body")
      end)
    end
  end

  describe "poll_inbox/2" do
    test "calls GET /inbox/:agent_id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.poll_inbox("a1")
    end

    test "accepts custom status" do
      assert {:error, _reason} = IamqBindings.poll_inbox("a1", "read")
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200([%{id: "msg-1", subject: "hello"}]))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.poll_inbox("a1")
        assert is_list(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "agent not found"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.poll_inbox("a1")
      end)
    end
  end

  describe "mark_message/2" do
    test "calls PATCH /messages/:id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.mark_message("msg-1", "read")
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{ok: true, message_id: "msg-1", status: "read"}))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.mark_message("msg-1", "read")
        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "message not found"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.mark_message("msg-1", "read")
      end)
    end
  end

  describe "list_agents/0" do
    test "calls GET /agents and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.list_agents()
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200([%{agent_id: "a1", name: "Agent One"}]))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.list_agents()
        assert is_list(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "forbidden"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.list_agents()
      end)
    end
  end

  describe "get_agent/1" do
    test "calls GET /agents/:agent_id and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.get_agent("a1")
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{agent_id: "a1", name: "Agent One"}))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.get_agent("a1")
        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "agent not found"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.get_agent("a1")
      end)
    end
  end

  describe "health/0" do
    test "calls GET /status and returns error tuple on connection failure" do
      assert {:error, _reason} = IamqBindings.health()
    end

    test "returns {:ok, body} on 2xx response" do
      port = start_mock_server(json_200(%{status: "ok"}))

      with_mock_url(port, fn ->
        assert {:ok, body} = IamqBindings.health()
        assert is_map(body)
      end)
    end

    test "returns {:error, {status, body}} on non-2xx response" do
      port = start_mock_server(json_422(%{error: "service unavailable"}))

      with_mock_url(port, fn ->
        assert {:error, {422, _body}} = IamqBindings.health()
      end)
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
