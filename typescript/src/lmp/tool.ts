import { ContentBlock } from '../types/message'
import { LMPType } from './types'

/**
 * Defines a tool for use in language model programs (LMPs) that support tool use.
 *
 * This decorator wraps a function, adding metadata and handling for tool invocations.
 * It automatically extracts the tool's description and parameters from the function's
 * JSDoc comments and type annotations, creating a structured representation for LMs to use.
 *
 * @param {Object} options - Configuration options for the tool
 * @param {boolean} [options.exemptFromTracking=false] - If true, the tool usage won't be tracked
 * @param {Object} [options.toolKwargs] - Additional keyword arguments for tool configuration
 * @returns {Function} A wrapped version of the original function, usable as a tool by LMs
 *
 * Requirements:
 * - Function must have fully typed arguments (serializable to JSON).
 * - Return value must be one of: string, JSON-serializable object, or List<ContentBlock>.
 * - All parameters must have type annotations.
 * - Complex types should be interfaces or classes.
 * - Function should have descriptive JSDoc comments.
 * - Can only be used in LMPs with @ell.complex decorators
 *
 * Functionality:
 * 1. Metadata Extraction:
 *    - Uses function JSDoc as tool description.
 *    - Extracts parameter info from type annotations and JSDoc.
 *    - Creates a schema for parameter validation and schema generation.
 *
 * 2. Integration with LMs:
 *    - Can be passed to @ell.complex decorators.
 *    - Provides structured tool information to LMs.
 *
 * 3. Invocation Handling:
 *    - Manages tracking, logging, and result processing.
 *    - Wraps results in appropriate types for tracking.
 *
 * Usage Modes:
 * 1. Normal Function Call:
 *    - Behaves like a regular TypeScript function.
 *    - Example: const result = myTool({ arg1: "value", arg2: 123 });
 *
 * 2. LMP Tool Call:
 *    - Used within LMPs or with explicit _toolCallId.
 *    - Returns a ToolResult object.
 *    - Example: const result = myTool({ arg1: "value", arg2: 123, _toolCallId: "unique_id" });
 *
 * Result Coercion:
 * - String → ContentBlock({ text: result })
 * - Object → ContentBlock({ parsed: result })
 * - List<ContentBlock> → Used as-is
 * - Other types → ContentBlock({ text: JSON.stringify(result) })
 *
 * Example:
 * ```typescript
 * interface ClaimDraftParams {
 *   claimDetails: string;
 *   claimType: string;
 *   claimAmount: number;
 *   claimDate: string; // Date format: YYYY-MM-DD
 * }
 *
 * @ell.tool()
 * function createClaimDraft(params: ClaimDraftParams): string {
 *   // Create a claim draft. Returns the created claim ID.
 *   return "12345";
 * }
 *
 * // For use in a complex LMP:
 * @ell.complex({ model: "gpt-4", tools: [createClaimDraft], temperature: 0.1 })
 * function insuranceChatbot(messageHistory: Message[]): Message[] {
 *   // Chatbot implementation...
 * }
 *
 * const x = insuranceChatbot([
 *   ell.user("I crashed my car into a tree."),
 *   ell.assistant("I'm sorry to hear that. Can you provide more details?"),
 *   ell.user("The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000")
 * ]);
 * console.log(x);
 * // Output:
 * // ell.Message({
 * //   content: [
 * //     ContentBlock({
 * //       toolCall: {
 * //         toolCallId: "asdas4e",
 * //         toolFn: createClaimDraft,
 * //         input: {
 * //           claimDetails: "The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000",
 * //           claimType: "car",
 * //           claimAmount: 5000,
 * //           claimDate: "2024-08-01"
 * //         }
 * //       }
 * //     })
 * //   ],
 * //   role: 'assistant'
 * // })
 *
 * if (x.toolCalls) {
 *   const nextUserMessage = responseMessage.callToolsAndCollectAsMessage();
 *   // This actually calls createClaimDraft
 *   console.log(nextUserMessage);
 *   // Output:
 *   // ell.Message({
 *   //   content: [
 *   //     ContentBlock({
 *   //       toolResult: {
 *   //         toolCallId: "asdas4e",
 *   //         result: [ContentBlock({ text: "12345" })]
 *   //       }
 *   //     })
 *   //   ],
 *   //   role: 'user'
 *   // })
 *
 *   const y = insuranceChatbot([...messageHistory, x, nextUserMessage]);
 *   console.log(y);
 *   // Output:
 *   // ell.Message({ content: "I've filed that for you!", role: 'assistant' })
 * }
 * ```
 *
 * Note:
 * - Tools are integrated into LMP calls via the 'tools' parameter in @ell.complex.
 * - LMs receive structured tool information, enabling understanding and usage within the conversation context.
 */
export const tool = <InputType extends Record<string, any>, OutputType extends any>(
  fn: (input: InputType) => Promise<OutputType>,
  options?: { excempt_from_tracking?: boolean }
) => {
  const wrapper = async (args: InputType, _invocation_origin?: string, _tool_call_id?: string) => {
    const result = await fn(args)
    if (!_tool_call_id) {
      return result // _invocation_api_params, {}
    }

    let content_results: ContentBlock[] = []

    try {
      if (result instanceof ContentBlock) {
        content_results = [result]
      } else if (Array.isArray(result) && result.every((c) => c instanceof ContentBlock)) {
        content_results = result
      } else {
        content_results = [new ContentBlock({ text: JSON.stringify(result) })]
      }
    } catch (e) {
      throw new Error(
        `Failed to convert tool use result to ContentBlock: ${e}. Tools must return json serializable objects. or a list of ContentBlocks.`
      )
    }
  }
  Object.defineProperty(wrapper, '__ell_tool_kwargs__', { value: options })
  Object.defineProperty(wrapper, '__ell_func__', { value: fn })
  Object.defineProperty(wrapper, '__ell_type__', { value: LMPType.TOOL })
  Object.defineProperty(wrapper, '__ell_exempt_from_tracking', { value: options?.excempt_from_tracking })

  try {
    // Create a zod type and assign

  } catch (e) {
    console.error("Failed to generate tool call params model")
  }

}













  return wrapper
}
