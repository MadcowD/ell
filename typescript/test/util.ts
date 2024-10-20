import OpenAI from "openai";

export const chatCompletionsToStream = (completions: OpenAI.Chat.Completions.ChatCompletion[]) => {
  return completions.map((completion):OpenAI.ChatCompletionChunk => {
    return {
      id: completion.id,
      created: completion.created,
      model: completion.model,
      object: 'chat.completion.chunk',
      choices: completion.choices.map((choice,i):OpenAI.ChatCompletionChunk.Choice => {
        return {
          delta: {
            content: choice.message.content,
            role: choice.message.role,
            refusal: choice.message.refusal,
          },
          index: choice.index || i,
          finish_reason: choice.finish_reason,
        }
      }),
    }
  })
}