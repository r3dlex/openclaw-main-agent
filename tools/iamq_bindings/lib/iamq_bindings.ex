defmodule IamqBindings do
  @moduledoc """
  Elixir client bindings for the IAMQ inter-agent messaging API.

  Every public function returns `{:ok, response_body}` on success or
  `{:error, reason}` on failure.
  """

  alias IamqBindings.Config

  # ---------------------------------------------------------------------------
  # Public API
  # ---------------------------------------------------------------------------

  @doc """
  Register an agent with the IAMQ system.
  """
  @spec register(String.t(), String.t(), String.t(), String.t(), list(String.t())) ::
          {:ok, map()} | {:error, term()}
  def register(agent_id, name, emoji, description, capabilities) do
    post("/register", %{
      agent_id: agent_id,
      name: name,
      emoji: emoji,
      description: description,
      capabilities: capabilities
    })
  end

  @doc """
  Send a heartbeat for the given agent.
  """
  @spec heartbeat(String.t()) :: {:ok, map()} | {:error, term()}
  def heartbeat(agent_id) do
    post("/heartbeat", %{agent_id: agent_id})
  end

  @doc """
  Send a message from one agent to another.

  ## Options

    * `:priority` — message priority (e.g. `"normal"`, `"high"`)
    * `:type` — message type
    * `:replyTo` — ID of the message being replied to

  """
  @spec send_message(String.t(), String.t(), String.t(), String.t(), keyword()) ::
          {:ok, map()} | {:error, term()}
  def send_message(from, to, subject, body, opts \\ []) do
    payload =
      %{from: from, to: to, subject: subject, body: body}
      |> maybe_put(:priority, Keyword.get(opts, :priority))
      |> maybe_put(:type, Keyword.get(opts, :type))
      |> maybe_put(:replyTo, Keyword.get(opts, :replyTo))

    post("/send", payload)
  end

  @doc """
  Poll the inbox for a given agent.

  `status` defaults to `"unread"`.
  """
  @spec poll_inbox(String.t(), String.t()) :: {:ok, list()} | {:error, term()}
  def poll_inbox(agent_id, status \\ "unread") do
    get("/inbox/#{agent_id}", status: status)
  end

  @doc """
  Update the status of a message (e.g. mark as read).
  """
  @spec mark_message(String.t(), String.t()) :: {:ok, map()} | {:error, term()}
  def mark_message(message_id, status) do
    patch("/messages/#{message_id}", %{status: status})
  end

  @doc """
  List all registered agents.
  """
  @spec list_agents() :: {:ok, list()} | {:error, term()}
  def list_agents do
    get("/agents")
  end

  @doc """
  Get details for a single agent.
  """
  @spec get_agent(String.t()) :: {:ok, map()} | {:error, term()}
  def get_agent(agent_id) do
    get("/agents/#{agent_id}")
  end

  @doc """
  Check system health.
  """
  @spec health() :: {:ok, map()} | {:error, term()}
  def health do
    get("/status")
  end

  # ---------------------------------------------------------------------------
  # Internal helpers
  # ---------------------------------------------------------------------------

  defp post(path, body) do
    url = Config.base_url() <> path

    case Req.post(url, json: body) do
      {:ok, %Req.Response{status: status, body: resp_body}} when status in 200..299 ->
        {:ok, resp_body}

      {:ok, %Req.Response{status: status, body: resp_body}} ->
        {:error, {status, resp_body}}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp get(path, params \\ []) do
    url = Config.base_url() <> path

    case Req.get(url, params: params) do
      {:ok, %Req.Response{status: status, body: resp_body}} when status in 200..299 ->
        {:ok, resp_body}

      {:ok, %Req.Response{status: status, body: resp_body}} ->
        {:error, {status, resp_body}}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp patch(path, body) do
    url = Config.base_url() <> path

    case Req.patch(url, json: body) do
      {:ok, %Req.Response{status: status, body: resp_body}} when status in 200..299 ->
        {:ok, resp_body}

      {:ok, %Req.Response{status: status, body: resp_body}} ->
        {:error, {status, resp_body}}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp maybe_put(map, _key, nil), do: map
  defp maybe_put(map, key, value), do: Map.put(map, key, value)
end
