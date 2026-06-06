ExUnit.start()

# `mix test --no-start` keeps the application tree down. The GenServer
# tests drive Req (which uses Finch) and Bypass, so their supervisors
# need to be up before tests run.
{:ok, _} = Application.ensure_all_started(:finch)
{:ok, _} = Application.ensure_all_started(:bypass)
{:ok, _} = Application.ensure_all_started(:req)
