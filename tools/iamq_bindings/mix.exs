defmodule IamqBindings.MixProject do
  use Mix.Project

  def project do
    [
      app: :iamq_bindings,
      version: "0.1.0",
      elixir: "~> 1.15",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      name: "IamqBindings",
      source_url: "https://github.com/r3dlex/openclaw-main-agent",
      docs: [
        main: "IamqBindings",
        extras:
          (if File.exists?("README.md"), do: ["README.md"], else: []) ++
            (if File.exists?("spec"), do: Path.wildcard("spec/*.md"), else: []),
        output: "doc/",
        formatters: ["html"]
      ],
      test_coverage: [summary: [threshold: 90]]
    ]
  end

  def application do
    [
      extra_applications: [:logger]
    ]
  end

  defp deps do
    [
      {:jason, "~> 1.4"},
      {:req, "~> 0.4"},
      {:ex_doc, "~> 0.34", only: :dev, runtime: false}
    ]
  end
end
