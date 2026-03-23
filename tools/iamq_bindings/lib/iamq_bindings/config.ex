defmodule IamqBindings.Config do
  @moduledoc """
  Configuration for the IAMQ HTTP API client.

  Reads `IAMQ_HTTP_URL` from the environment, falling back to
  `http://127.0.0.1:18790` when the variable is not set.
  """

  @default_base_url "http://127.0.0.1:18790"
  @default_agent_id "main"

  @doc """
  Returns the base URL for the IAMQ API.
  """
  @spec base_url() :: String.t()
  def base_url do
    System.get_env("IAMQ_HTTP_URL") || @default_base_url
  end

  @doc """
  Returns this agent's IAMQ agent ID.
  """
  @spec agent_id() :: String.t()
  def agent_id do
    System.get_env("IAMQ_AGENT_ID") || @default_agent_id
  end
end
