defmodule IamqSidecar.MixProject do
  use Mix.Project

  def project do
    [
      app: :iamq_sidecar,
      version: "0.1.0",
      elixir: "~> 1.18",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      aliases: aliases(),
      # Transitional floor for the iamq/ subproject — the vendored
      # sidecar has no real test suite yet. The cron HTTP paths
      # (list_crons, register_cron, get_cron, update_cron,
      # delete_cron) are covered by mq_client_test.exs; the
      # GenServer's HTTP paths (do_get, do_register, do_heartbeat,
      # do_poll_inbox, do_send, do_ack) require a real IAMQ endpoint
      # or a Bypass server. Drive this floor up to 90% in a
      # follow-up. See the openclaw-main-agent follow-up issue
      # "iamq/: drive coverage to 90%".
      test_coverage: [summary: [threshold: 5]],
      description: description(),
      docs: docs()
    ]
  end

  def application do
    [
      extra_applications: [:logger],
      mod: {IamqSidecar.Application, []}
    ]
  end

  defp aliases do
    [
      test: ["test --no-start"]
    ]
  end

  defp deps do
    [
      {:jason, "~> 1.4"},
      {:req, "~> 0.5"},
      {:websockex, "~> 0.5"},
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: [:dev, :test], runtime: false},
      {:sobelow, "~> 0.13", only: [:dev, :test], runtime: false},
      {:doctor, "~> 0.21", only: [:dev, :test], runtime: false},
      {:excoveralls, "~> 0.18", only: :test, runtime: false}
    ]
  end

  defp description do
    """
    IAMQ HTTP + WebSocket sidecar for the OpenClaw main agent.

    Provides a supervised GenServer pair (`IamqSidecar.MqClient` /
    `IamqSidecar.MqWsClient`) and a Telegram delivery helper
    (`IamqSidecar.Gateway.Client`) for forwarding inbound IAMQ
    messages to the OpenClaw gateway.
    """
  end

  defp docs do
    [
      main: "readme",
      source_url: "https://github.com/r3dlex/openclaw-main-agent",
      extras: []
    ]
  end
end
