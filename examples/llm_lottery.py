#!/usr/bin/env python3

# Tip: Most fun when run with `-v` or `-vv` flag!
#
# Small educational example on how to use tools.
# The example provides LLM with two tools:
# * One to buy a lottery ticket.
# * Another to check a lottery ticket.
# 
# Then we run LLM to enjoy watching how it plays the lottery.
#
# Additionally, it provides:
# `loop_llm_and_tools` - an example of a handy boilerplate function
#                        that helps to run tools until the task is completed.
# `main` with argparse and -v|--verbose flag -
#        An example of how to make simple code convenient to switch between
#        different verbosity levels from the command line, e.g. for this script:
#        * `-v`  prints progress information to stderr.
#        * `-vv` also enables verbosity for ell.init.

import ell
from ell import Message
import argparse
import sys
from typing import List
from pydantic import Field

VERBOSE = False
WINNING_NUMBER = 12  # Hardcoded winning number

@ell.tool(strict=True)
def buy_lottery_ticket(number: int = Field(description="Number to play in the lottery (0-16).")):
    """Buy a lottery ticket with the given number."""
    if VERBOSE:
        sys.stderr.write(f"Calling tool: buy_lottery_ticket({number})\n")
    return f"Bought lottery ticket with number {number}"

@ell.tool(strict=True)
def check_lottery_result(number: int = Field(description="Number to check against the lottery result.")):
    """Check if the given number wins the lottery."""
    if VERBOSE:
        sys.stderr.write(f"Calling tool: check_lottery_result({number})\n")
    if number == WINNING_NUMBER:
        return "Congratulations! You won the lottery!"
    else:
        return "Sorry, your number did not win. Try again!"

@ell.complex(model="gpt-4o-mini", tools=[buy_lottery_ticket, check_lottery_result])
def play_lottery(message_history: List[Message]) -> List[Message]:
    if VERBOSE:
        last_msg = message_history[-1].text
        sys.stderr.write(f"Calling LMP: play_lottery('{last_msg}')\n")
    return [
        ell.system("You are an AI assistant that plays the lottery. Buy a lottery ticket with a number between 0 and 16, then check if it wins. If it doesn't win, try again with a different number.")
    ] + message_history

def loop_llm_and_tools(f, message_history, max_iterations=100):
    iteration = 0
    while iteration < max_iterations:
        response_message = f(message_history)
        message_history.append(response_message)

        if response_message.tool_calls:
            tool_call_response = response_message.call_tools_and_collect_as_message()
            message_history.append(tool_call_response)
            
            # Check if we've won the lottery
            if "Congratulations" in tool_call_response.text:
                break
        else:
            break
        iteration += 1
    return message_history

def main():
    parser = argparse.ArgumentParser(description='Play the lottery until winning.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level')
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose > 0

    ell.init(verbose=(args.verbose > 1), store='./logdir', autocommit=True)

    message_history = []
    message_history.append(ell.user("Let's play the lottery until we win!"))

    message_history = loop_llm_and_tools(play_lottery, message_history)

    print("\nLottery Game Results:")
    for message in message_history:
        if message.role == "assistant" or message.role == "function":
            print(f"{message.role.capitalize()}: {message.text}")

    print(f"\nTotal attempts: {len(message_history) // 2 - 1}")

if __name__ == "__main__":
    main()

