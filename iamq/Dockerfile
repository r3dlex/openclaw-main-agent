FROM elixir:1.18-slim AS build
RUN apt-get update -qq && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
RUN mix local.hex --force && mix local.rebar --force
WORKDIR /app
COPY mix.exs mix.lock* ./
RUN mix deps.get && mix deps.compile
COPY lib/ lib/
RUN MIX_ENV=prod mix compile

FROM elixir:1.18-slim
RUN apt-get update -qq && apt-get install -y --no-install-recommends ca-certificates curl gnupg && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs && npm install -g openclaw
RUN mix local.hex --force && mix local.rebar --force
WORKDIR /app
COPY --from=build /app/ /app/
CMD ["mix", "run", "--no-halt"]
