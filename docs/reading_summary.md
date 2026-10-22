# MCP reading and server exploration

**Rana Ezzeddine | EECE 503P | C5**

## Summary

The Hugging Face article presents MCP as an open integration standard addressing a practical limitation: language models cannot reliably access changing external information through training alone. Without a shared interface, developers repeatedly build custom connections between assistants and services. MCP moves this integration work behind reusable servers, making contextual information and executable capabilities discoverable through a consistent protocol. The article frames this as infrastructure for useful agents rather than a replacement for the language model itself.

The linked full article situates MCP within agent workflows: agents need both relevant context and ways to act on it. Standardization improves interoperability, but does not remove the need to choose suitable capabilities or control access. A working connection is therefore only the beginning; developers must still decide what information the model receives and which effects it may trigger.

The official architecture clarifies three distinct responsibilities. The Host is the AI application coordinating model interaction and access policies. It creates a Client for each connected Server. The Client handles protocol communication, while the Server exposes capabilities backed by a particular service. Tools are callable operations; resources provide contextual data; prompts supply reusable interaction templates. Tool discovery and execution are separate operations, allowing a host to inspect names, descriptions, and schemas before making a call.

I explored the reference filesystem server's startup and tool-registration modules. Its read_text_file tool has a focused purpose, typed path and optional head/tail arguments, an output schema, and a description explaining its directory restrictions. The handler rejects simultaneous head and tail requests. The write_file tool separately declares that it can overwrite content and marks itself as destructive. Keeping these operations distinct makes their effects easier to understand and govern.

The design is not uniformly minimal. read_multiple_files batches several reads into one call, trading a larger response and per-file error handling for fewer round trips. This remains one coherent responsibility, rather than an unrelated collection of actions. A sharper concern is the deprecated read_file alias: exposing two names for the same operation can make tool selection less predictable. My toolkit instead exposes exactly three names with explicit categories, while its orchestration reuses the smaller capabilities. The lesson is that single-purpose design depends on clear behavioral boundaries, not simply the number of internal steps.

## Sources and exploration scope

- Assigned article: https://huggingface.co/blog/Kseniase/mcp
- Full article linked from the assigned page: https://www.turingpost.com/p/mcp
- Architecture clarification: https://modelcontextprotocol.io/docs/learn/architecture
- Inspected filesystem startup: https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/index.ts
- Inspected tool schemas, handlers and annotations: https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/server.ts

The server exploration was a source review, not a claim that the reference server was executed. Sources were accessed on October 22, 2026. The assigned Hugging Face page contains an introduction and links to the full article, so the two are distinguished above.
