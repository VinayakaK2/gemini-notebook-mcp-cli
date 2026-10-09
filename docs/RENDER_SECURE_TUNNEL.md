# Render deployment: NotebookLM MCP through OpenAI Secure MCP Tunnel

This configuration keeps NotebookLM MCP on stdio and lets OpenAI's tunnel-client
connect to it outbound. The Render public port is used only for a minimal
health endpoint; do not configure ChatGPT with the Render URL.

## 1. Render environment variables

In Render Dashboard → the new tunnel service → Environment, set:

- `CONTROL_PLANE_TUNNEL_ID`: `tunnel_6ac90a67956c8191ac7650b9635e6be4`
- `CONTROL_PLANE_API_KEY`: your OpenAI **Runtime API key** with Tunnels Read + Use.
- `NOTEBOOKLM_COOKIES`: a valid NotebookLM/Google cookie value in the format supported by this repository's Authentication Guide.

Set secret values directly in Render's dashboard. Do not commit keys or cookies to GitHub, and do not paste them into chat. Do not use an OpenAI admin key as the long-lived runtime key.

## 2. Create the Render service

1. Merge the secure-tunnel branch into `main` after reviewing the changes.
2. In Render Dashboard, create a **new Web Service** from this GitHub repository. Keep the existing failing Python service untouched until the new one passes tests.
3. Choose branch `main`, runtime **Docker**, Dockerfile path `./Dockerfile`, region Singapore, and Free plan for initial testing.
4. Set Health Check Path to `/healthz`.
5. Add the three environment variables above. Never add the runtime key or cookies to the repository or Blueprint YAML.
6. Deploy. Check build and runtime logs. `/healthz` should return 200 only when the tunnel-client health endpoint reports ready.

## 3. Connect ChatGPT

1. Ensure the tunnel-client is running and healthy.
2. Open [ChatGPT connector settings](https://chatgpt.com/#settings/Connectors).
3. Add a custom MCP server using the **Tunnel** option and select/use the tunnel ID above. Do not use the public Render URL as the MCP endpoint.
4. Test by asking ChatGPT to list your NotebookLM notebooks and read a source from a notebook you choose.

## 4. Important limitations

- This branch has not been live-tested with your runtime key or Google session. Do not treat a successful Docker build as proof of NotebookLM access.
- `NOTEBOOKLM_COOKIES` is a session credential and may expire. Google may require interactive sign-in again. Refresh it securely in Render Environment settings if authentication fails.
- Render Free may sleep after inactivity. For dependable availability, use an always-on plan.
- Only one active tunnel-client process should use this tunnel ID with the stdio `--mcp.command` binding. Avoid overlapping deploy instances during restarts.
- Do not set `NOTEBOOKLM_ALLOW_EXTERNAL_BIND=1`; this configuration uses stdio and does not expose the MCP HTTP/SSE endpoint.
