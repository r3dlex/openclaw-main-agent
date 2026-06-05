defmodule IamqSidecar.Gateway.Client do
  @moduledoc """
  Ephemeral WebSocket client that connects to the OpenClaw gateway,
  sends a Telegram notification, then disconnects.

  Designed for fire-and-forget delivery: connect → authenticate → send → close.
  """
  use WebSockex

  require Logger

  @default_gateway_url "ws://127.0.0.1:18789/ws"

  # --- public API ---

  @doc """
  Send a Telegram message via the OpenClaw gateway.
  Returns :ok or {:error, reason}.
  """
  def send_telegram(message) do
    gateway_url = System.get_env("OPENCLAW_GATEWAY_URL", @default_gateway_url)
    token = System.get_env("OPENCLAW_GATEWAY_TOKEN", "")
    account = System.get_env("OPENCLAW_TELEGRAM_ACCOUNT", "oc_gr_mq_bot")

    if token == "" do
      Logger.warning("[Gateway] OPENCLAW_GATEWAY_TOKEN not set — skipping Telegram delivery")
      {:error, :no_token}
    else
      content = format_message(message)

      # Try WS RPC first; if it fails, fall back to CLI
      result = try_ws_rpc(gateway_url, token, account, content)

      case result do
        :ok ->
          Logger.info("[Gateway] Telegram delivery via WS RPC")
          :ok

        {:error, reason} ->
          Logger.warning("[Gateway] WS RPC failed (#{inspect(reason)}) — trying CLI fallback")
          try_cli_fallback(account, content)
      end
    end
  end

  defp try_ws_rpc(gateway_url, token, account, content) do
    # André's Telegram chat ID — default target for all Telegram deliveries
    andre_telegram_id = "5887382088"

    payload = %{
      account: account,
      channel: "telegram",
      content: content,
      deliver: true,
      target: andre_telegram_id
    }

    # Synchronous WS RPC — blocks up to 15s then returns
    case start_link_sync(gateway_url, token, payload) do
      {:ok, _pid} -> :ok
      {:error, reason} -> {:error, reason}
    end
  end

  defp start_link_sync(gateway_url, token, payload) do
    caller = self()

    _spawn_result = spawn_monitor(fn ->
      case start_link({gateway_url, token, payload, self()}) do
        {:ok, _pid} ->
          receive do
            {:gateway_result, result} ->
              send(caller, {:gateway_result, result})
          after
            15_000 ->
              send(caller, {:gateway_result, {:error, :timeout}})
          end

        {:error, reason} ->
          send(caller, {:gateway_result, {:error, reason}})
      end
    end)

    receive do
      {:gateway_result, result} -> result
    after
      20_000 -> {:error, :timeout}
    end
  end

  defp try_cli_fallback(_account, content) do
    # Inside Docker, we need host.docker.internal to reach the gateway.
    # Pass the token explicitly so the CLI doesn't require interactive auth.
    gateway_token = System.get_env("OPENCLAW_GATEWAY_TOKEN", "")
    Logger.info("[Gateway] CLI fallback: openclaw agent --agent main --message #{inspect(content)}")

    env = [
      {"OPENCLAW_GATEWAY_URL", "ws://host.docker.internal:18789"},
      {"OPENCLAW_GATEWAY_TOKEN", gateway_token}
    ]

    {output, exit_code} = System.cmd("openclaw", [
      "agent", "--agent", "main",
      "--message", content
    ], env: env)

    if exit_code == 0 do
      Logger.info("[Gateway] CLI fallback succeeded")
      :ok
    else
      Logger.warning("[Gateway] CLI fallback failed: #{String.trim(output)}")
      write_inbox_fallback(content)
    end
  end

  defp write_inbox_fallback(content) do
    # Last resort: write to the main agent inbox file
    inbox_path = Path.join(System.get_env("HOME", "/root"), ".openclaw/workspace/queue/main/.pending")

    with :ok <- File.mkdir_p(Path.dirname(inbox_path)),
         :ok <- File.write(inbox_path, "[IAMQ fallback] #{content}\n", [:append]) do
      Logger.info("[Gateway] Wrote to inbox fallback: #{inbox_path}")
      :ok
    else
      {:error, reason} ->
        Logger.error("[Gateway] Inbox fallback failed: #{inspect(reason)}")
        {:error, :inbox_fallback_failed}
    end
  end

  # --- WebSockex callbacks ---

  def start_link({gateway_url, token, delivery_payload, caller}) do
    state = %{
      gateway_url: gateway_url,
      token: token,
      delivery_payload: delivery_payload,
      caller: caller,
      req_id: 1,
      status: :idle
    }

    WebSockex.start_link(gateway_url, __MODULE__, state, name: __MODULE__)
  end

  @impl true
  def handle_connect(_conn, state) do
    Logger.info("[Gateway] WS connected to #{state.gateway_url}, waiting for challenge")
    {:ok, %{state | status: :waiting_challenge}}
  end

  @impl true
  def handle_frame({:text, frame}, state) do
    case Jason.decode(frame) do
      {:ok, %{"type" => "event", "event" => "connect.challenge", "payload" => payload}} ->
        Logger.info("[Gateway] Received connect.challenge")
        handle_challenge(payload, state)

      {:ok, %{"type" => "res", "id" => id, "ok" => true, "payload" => payload}} ->
        Logger.info("[Gateway] Received res id=#{id} ok=true payload=#{inspect(payload)}")
        handle_auth_response(id, payload, state)

      {:ok, %{"type" => "res", "id" => _id, "ok" => false, "payload" => payload}} ->
        Logger.warning("[Gateway] Gateway returned error: #{inspect(payload)}")
        send(state.caller, {:gateway_result, {:error, payload}})
        {:close, %{state | status: :closing}}

      {:ok, %{"event" => event}} ->
        Logger.info("[Gateway] Unexpected event: #{event}")
        {:ok, state}

      other ->
        Logger.warning("[Gateway] Unexpected frame: #{inspect(other)}")
        {:ok, state}
    end
  rescue
    e ->
      Logger.error("[Gateway] Exception in handle_frame: #{inspect(e)}")
      send(state.caller, {:gateway_result, {:error, "frame handler exception: #{inspect(e)}"}})
      {:close, %{state | status: :closing}}
  end

  def handle_frame(other, state) do
    Logger.warning("[Gateway] Unexpected frame type: #{inspect(other)}")
    {:ok, state}
  end

  @impl true
  def handle_disconnect(reason, state) do
    Logger.warning("[Gateway] WS disconnected: #{inspect(reason)}")
    send(state.caller, {:gateway_result, {:error, "disconnected: #{inspect(reason)}"}})
    {:ok, %{state | status: :done}}
  end

  # --- Challenge handling ---

  defp handle_challenge(%{"nonce" => nonce, "ts" => _ts}, state) do
    identity = load_or_generate_identity()
    Logger.info("[Gateway] Identity loaded, deviceId=#{inspect(identity["deviceId"])}")

    signed_at_ms = System.system_time(:millisecond)
    scopes = []

    device_auth_payload = build_device_auth_payload_v3(%{
      device_id: identity["deviceId"],
      client_id: "gateway-client",
      client_mode: "backend",
      role: "operator",
      scopes: scopes,
      signed_at_ms: signed_at_ms,
      token: state.token,
      nonce: nonce,
      platform: "elixir",
      device_family: "server"
    })

    signature = :crypto.sign(:eddsa, :none, device_auth_payload, [identity["private_key"], :ed25519])
    signature_b64 = Base.url_encode64(signature, padding: false)

    connect_req = %{
      "type" => "req",
      "id" => Integer.to_string(state.req_id),
      "method" => "connect",
      "params" => %{
        "minProtocol" => 3,
        "maxProtocol" => 3,
        "client" => %{
          "id" => "gateway-client",
          "version" => "1.0.0",
          "platform" => "elixir",
          "mode" => "backend"
        },
        "role" => "operator",
        "scopes" => scopes,
        "auth" => %{"token" => state.token},
        "device" => %{
          "id" => identity["deviceId"],
          "nonce" => nonce,
          "publicKey" => Base.url_encode64(identity["public_key"], padding: false),
          "signature" => signature_b64,
          "signedAt" => signed_at_ms
        }
      }
    }

    Logger.info("[Gateway] Sending connect.req with device auth")
    {:reply, {:text, Jason.encode!(connect_req)}, %{state | req_id: state.req_id + 1}}
  rescue
    e ->
      Logger.error("[Gateway] handle_challenge exception: #{inspect(e)}")
      send(state.caller, {:gateway_result, {:error, "challenge handler exception: #{inspect(e)}"}})
      {:close, %{state | status: :closing}}
  end

  defp handle_auth_response(_id, %{"type" => "hello-ok", "protocol" => 3}, state) do
    Logger.info("[Gateway] Auth successful — sending gateway.send RPC")

    %{account: account, channel: channel, content: content, deliver: deliver} =
      state.delivery_payload

    # Extract target from payload (André's Telegram chat ID)
    target = Map.get(state.delivery_payload, :target, "5887382088")

    send_req = %{
      "type" => "req",
      "id" => Integer.to_string(state.req_id),
      "method" => "gateway.send",
      "params" => %{
        "account" => account,
        "channel" => channel,
        "content" => content,
        "deliver" => deliver,
        "target" => target
      }
    }

    {:reply, {:text, Jason.encode!(send_req)}, %{state | req_id: state.req_id + 1, status: :authenticated}}
  end

  defp handle_auth_response(id, payload, state) do
    Logger.warning("[Gateway] Unexpected auth response id=#{id} payload=#{inspect(payload)}")
    send(state.caller, {:gateway_result, {:error, "unexpected auth response"}})
    {:close, %{state | status: :closing}}
  end

  # --- helpers ---

  # Extract raw private key bytes from PKCS#8 Ed25519 PEM
  # PKCS#8 Ed25519 parses as {:ECPrivateKey, 1, priv_bytes, {:namedCurve, {1,3,101,112}}, :asn1_NOVALUE, :asn1_NOVALUE}
  defp decode_pem_private_key(pem_string) do
    [pem_entry] = :public_key.pem_decode(pem_string)
    decoded = :public_key.pem_entry_decode(pem_entry)
    {:ECPrivateKey, _version, priv_bytes, _curve, :asn1_NOVALUE, :asn1_NOVALUE} = decoded
    priv_bytes
  end

  # Extract raw public key bytes from PEM (P-256 ECPoint)
  defp decode_pem_public_key(pem_string) do
    [pem_entry] = :public_key.pem_decode(pem_string)
    {{:ECPoint, pub_bytes}, {:namedCurve, _oid}} = :public_key.pem_entry_decode(pem_entry)
    pub_bytes
  end

  # Load device identity for gateway authentication.
  # System device.json is used first (paired identity).
  # IAMQ-specific identity is used when device.json is not available.
  defp load_or_generate_identity do
    # IAMQ-specific identity takes precedence — it uses the token registered in paired.json
    iamq_path = Path.join(System.get_env("HOME", "/root"), ".openclaw/iamq-device-identity.json")

    if File.exists?(iamq_path) do
      Logger.info("[Gateway] Loading IAMQ identity from: #{iamq_path}")
      load_iamq_device_identity(iamq_path)
    else
      # Fallback: system device identity (PKCS#8 PEM)
      identity_path = Path.join(System.get_env("HOME", "/root"), ".openclaw/identity/device.json")
      Logger.info("[Gateway] No IAMQ identity — trying system device at #{identity_path}")
      load_system_device_identity(identity_path)
    end
  rescue
    e ->
      Logger.warning("[Gateway] Failed to load identity: #{inspect(e)} — generating fresh IAMQ identity")
      iamq_path = Path.join(System.get_env("HOME", "/root"), ".openclaw/iamq-device-identity.json")
      generate_and_persist_identity(iamq_path)
  end

  # Load system device identity (PKCS#8 PEM format) from device.json
  defp load_system_device_identity(path) do
    Logger.info("[Gateway] Loading system device identity from: #{path}")

    with {:ok, body} <- File.read(path),
         {:ok, json} <- Jason.decode(body),
         private_key <- decode_pem_private_key(json["privateKeyPem"]),
         public_key <- decode_pem_public_key(json["publicKeyPem"]) do
      device_id = json["deviceId"]
      Logger.info("[Gateway] System device loaded: deviceId=#{device_id}, pubKey bytes=#{byte_size(public_key)}, privKey bytes=#{byte_size(private_key)}")
      %{
        "deviceId" => device_id,
        "private_key" => private_key,
        "public_key" => public_key
      }
    else
      {:error, reason} ->
        Logger.error("[Gateway] Failed to read system device identity: #{inspect(reason)}")
        raise "Cannot load system device identity: #{inspect(reason)}"
      {:error, _, _} ->
        Logger.error("[Gateway] Failed to parse system device identity JSON")
        raise "Cannot parse system device identity JSON"
      _ ->
        Logger.error("[Gateway] Unexpected error loading system device identity")
        raise "Unexpected error loading system device identity"
    end
  end

  defp generate_and_persist_identity(path) do
    Logger.info("[Gateway] No IAMQ identity found at #{path} — generating fresh Ed25519 keypair")

    {pub_key, priv_key} = :crypto.generate_key(:eddsa, :ed25519)
    device_id = :crypto.hash(:sha256, pub_key) |> Base.encode16(case: :lower)

    json = %{
      "device_id" => device_id,
      "public_key" => Base.url_encode64(pub_key, padding: false),
      "private_key" => Base.url_encode64(priv_key, padding: false)
    }

    # Ensure directory exists
    Path.dirname(path) |> File.mkdir_p()

    case File.write(path, Jason.encode!(json)) do
      :ok ->
        Logger.info("[Gateway] Identity persisted to #{path}, deviceId=#{device_id}")
        load_iamq_device_identity(path)

      {:error, reason} ->
        Logger.error("[Gateway] Failed to persist identity: #{inspect(reason)}")
        raise "Cannot persist IAMQ device identity: #{inspect(reason)}"
    end
  end

  defp load_iamq_device_identity(path) do
    Logger.info("[Gateway] Loading IAMQ identity from: #{path}")

    with {:ok, body} <- File.read(path),
         {:ok, json} <- Jason.decode(body),
         {:ok, private_key} <- Base.url_decode64(Map.get(json, "private_key"), padding: false),
         {:ok, public_key} <- Base.url_decode64(Map.get(json, "public_key"), padding: false) do
      device_id = Map.get(json, "device_id")
      Logger.info("[Gateway] IAMQ identity loaded: deviceId=#{device_id}, pubKey bytes=#{byte_size(public_key)}, privKey bytes=#{byte_size(private_key)}")
      %{
        "deviceId" => device_id,
        "private_key" => private_key,
        "public_key" => public_key
      }
    else
      {:error, reason} ->
        Logger.error("[Gateway] Failed to read IAMQ identity file: #{inspect(reason)}")
        raise "Cannot load IAMQ device identity: #{inspect(reason)}"
    end
  end

  defp build_device_auth_payload_v3(params) do
    scopes_str = Enum.join(params.scopes, ",")

    [
      "v3",
      params.device_id,
      params.client_id,
      params.client_mode,
      params.role,
      scopes_str,
      Integer.to_string(params.signed_at_ms),
      params.token || "",
      params.nonce,
      params.platform,
      params.device_family
    ]
    |> Enum.join("|")
  end

  defp format_message(msg) when is_map(msg) do
    from = msg["from"] || "unknown agent"
    subject = msg["subject"] || ""
    body = msg["body"] || ""

    # Handle gitrepo deliver_report action — extract report content directly
    if msg["body"] do
      try do
        body_json = Jason.decode!(msg["body"])
        if body_json["action"] == "deliver_report" && body_json["report"] do
          report = body_json["report"]
          content = report["content"] || ""
          filename = report["filename"] || ""
          return_content = "📊 *#{filename}*\n\n#{content}"
          "[GitRepo] Weekly Report from #{from}\n#{return_content}"
        else
          "[IAMQ] #{from}: #{subject}" <> (if body != "", do: "\n#{body}", else: "")
        end
      rescue
        _ -> "[IAMQ] #{from}: #{subject}" <> (if body != "", do: "\n#{body}", else: "")
      end
    else
      "[IAMQ] #{from}: #{subject}"
    end
  end

  defp format_message(_), do: "[IAMQ] New message received"

end
