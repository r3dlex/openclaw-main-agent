FROM elixir:1.16-alpine

RUN apk add --no-cache git

WORKDIR /app

# Install hex and rebar
RUN mix local.hex --force && \
    mix local.rebar --force

# Copy dependency manifests first for layer caching
COPY mix.exs mix.lock* ./

# Fetch and compile dependencies
RUN mix deps.get && mix deps.compile

# Copy application source
COPY lib lib/
COPY test test/

# Compile the project
RUN mix compile

CMD ["mix", "test"]
