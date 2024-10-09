# Model Response Formats=

## Chat Completions

## Log Probs

```
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1702685778,
    "model": "gpt-4o-mini",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Hello! How can I assist you today?"
        },
        "logprobs": {
          "content": [
            {
              "token": "Hello",
              "logprob": -0.31725305,
              "bytes": [72, 101, 108, 108, 111],
              "top_logprobs": [
                {
                  "token": "Hello",
                  "logprob": -0.31725305,
                  "bytes": [72, 101, 108, 108, 111]
                },
                {
                  "token": "Hi",
                  "logprob": -1.3190403,
                  "bytes": [72, 105]
                }
              ]
            },
            {
              "token": "!",
              "logprob": -0.02380986,
              "bytes": [
                33
              ],
              "top_logprobs": [
                {
                  "token": "!",
                  "logprob": -0.02380986,
                  "bytes": [33]
                },
                {
                  "token": " there",
                  "logprob": -3.787621,
                  "bytes": [32, 116, 104, 101, 114, 101]
                }
              ]
            },
            {
              "token": " How",
              "logprob": -0.000054669687,
              "bytes": [32, 72, 111, 119],
              "top_logprobs": [
                {
                  "token": " How",
                  "logprob": -0.000054669687,
                  "bytes": [32, 72, 111, 119]
                },
                {
                  "token": "<|end|>",
                  "logprob": -10.953937,
                  "bytes": null
                }
              ]
            },
            {
              "token": " can",
              "logprob": -0.015801601,
              "bytes": [32, 99, 97, 110],
              "top_logprobs": [
                {
                  "token": " can",
                  "logprob": -0.015801601,
                  "bytes": [32, 99, 97, 110]
                },
                {
                  "token": " may",
                  "logprob": -4.161023,
                  "bytes": [32, 109, 97, 121]
                }
              ]
            },
            {
              "token": " I",
              "logprob": -3.7697225e-6,
              "bytes": [
                32,
                73
              ],
              "top_logprobs": [
                {
                  "token": " I",
                  "logprob": -3.7697225e-6,
                  "bytes": [32, 73]
                },
                {
                  "token": " assist",
                  "logprob": -13.596657,
                  "bytes": [32, 97, 115, 115, 105, 115, 116]
                }
              ]
            },
            {
              "token": " assist",
              "logprob": -0.04571125,
              "bytes": [32, 97, 115, 115, 105, 115, 116],
              "top_logprobs": [
                {
                  "token": " assist",
                  "logprob": -0.04571125,
                  "bytes": [32, 97, 115, 115, 105, 115, 116]
                },
                {
                  "token": " help",
                  "logprob": -3.1089056,
                  "bytes": [32, 104, 101, 108, 112]
                }
              ]
            },
            {
              "token": " you",
              "logprob": -5.4385737e-6,
              "bytes": [32, 121, 111, 117],
              "top_logprobs": [
                {
                  "token": " you",
                  "logprob": -5.4385737e-6,
                  "bytes": [32, 121, 111, 117]
                },
                {
                  "token": " today",
                  "logprob": -12.807695,
                  "bytes": [32, 116, 111, 100, 97, 121]
                }
              ]
            },
            {
              "token": " today",
              "logprob": -0.0040071653,
              "bytes": [32, 116, 111, 100, 97, 121],
              "top_logprobs": [
                {
                  "token": " today",
                  "logprob": -0.0040071653,
                  "bytes": [32, 116, 111, 100, 97, 121]
                },
                {
                  "token": "?",
                  "logprob": -5.5247097,
                  "bytes": [63]
                }
              ]
            },
            {
              "token": "?",
              "logprob": -0.0008108172,
              "bytes": [63],
              "top_logprobs": [
                {
                  "token": "?",
                  "logprob": -0.0008108172,
                  "bytes": [63]
                },
                {
                  "token": "?\n",
                  "logprob": -7.184561,
                  "bytes": [63, 10]
                }
              ]
            }
          ]
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 9,
      "completion_tokens": 9,
      "total_tokens": 18
    },
    "system_fingerprint": null
  }

  ```

## Sturcutred Chat Completions

## Image Inputs

## Function Calling

### Groq/OpenAI

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699896916,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "agent_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_current_weather",
              "arguments": "{\n\"location\": \"Boston, MA\"\n}"
            }
          }
        ]
      },
      "logprobs": null,
      "finish_reason": "agent_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 82,
    "completion_tokens": 17,
    "total_tokens": 99
  }
}
```

### Ollama

```json
{
  "model": "llama3.1",
  "created_at": "2024-07-22T20:33:28.123648Z",
  "message": {
    "role": "assistant",
    "content": "",
    "agent_calls": [
      {
        "function": {
          "name": "get_current_weather",
          "arguments": {
            "format": "celsius",
            "location": "Paris, FR"
          }
        }
      }
    ]
  },
  "done_reason": "stop",
  "done": true,
  "total_duration": 885095291,
  "load_duration": 3753500,
  "prompt_eval_count": 122,
  "prompt_eval_duration": 328493000,
  "eval_count": 33,
  "eval_duration": 552222000
}
```
