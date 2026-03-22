defmodule IamqBindings.Config do
  @moduledoc """
  Configuration for the IAMQ HTTP API client.

  Reads `IAMQ_BASE_URL` from the environment, falling back to
  `http://127.0.0.1:18790` when the variable is not set.
  """

  @default_base_url "http://127.0.0.1:18790"

  @doc """
  Returns the base URL for the IAMQ API.
  """
  @spec base_url() :: String.t()
  def base_url do
    System.get_env("IAMQ_BASE_URL") || @default_base_url
  end
end
