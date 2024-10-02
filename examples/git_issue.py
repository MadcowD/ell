import ell
import os

from ell.stores.sql import SQLiteStore



@ell.simple(model="gpt-4o-mini", temperature=0.1)
def generate_description(about : str):
    return [
        ell.system(f"""Provide a clear and concise description of what the issue is. Include any relevant information that helps to explain the problem. 
                   This section should help the reader understand the context and the impact of the issue. 
                   Output only the description as a string and nothing else"""),
        ell.user(f"Generate a issue description about {about}."),
    ]

@ell.simple(model="gpt-4o-mini", temperature=0.1)
def generate_python_code_for_A_output_B(A: str, B: str = 'nothing'):
    return [
        ell.system(f"""You are a world-class python developer. Do not include code that can leak important privacy information that maybe of concern.
                   Check the code carefully in terms of correctness, style and efficiency. 
                   Do not format in markdown. You are directly outputting python code. 
                   Do not include use code to get system information that is not important to github issue.
                   You can also do multiline code if you need ot import any dependency. Do not write wrap any code in functions.
                    """),
        ell.user(f"Write the python code for {A} and the code should have a local 'OUTPUT' as {B}. Only output the code and nothing else."),
    ]

@ell.simple(model="gpt-4o", temperature=0.1)
def generate_issue(
                    error: str,
                   ):
        #generate description
    description = generate_description(error)

    # Define topics for system information
    info_topics = ['operating system info', 
                'Hardware',
                ]
                
    # Generate Python code for each info topic
    ls_code = [generate_python_code_for_A_output_B(i, 'string') for i in info_topics]
    system_info = []
    # Execute each generated code snippet
    for code in ls_code:
        local_vars = {}
        exec(code, globals(), local_vars)
        # Record the output 
        system_info.append(local_vars.get("OUTPUT"))
    
    return [
        ell.system("You are an expert at Markdown and at writing git issues. Output Markdown and nothing else"),
        ell.user(f"Write a git issue with the following description: {description}. Here is the system information: {system_info}"),
    ]

if __name__ == "__main__":

    ell.init(store='./logdir', autocommit=True, verbose=True)

    # This is an example from ell's early day error
    error_console_output = """
    (ell_lab) D:\\dev\\ell>D:/anaconda/envs/ell_lab/python.exe d:/dev/ell/examples/multilmp.py
    before ideas 1232131
    ╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║ generate_story_ideas(a dog) # (notimple...)
    ╠═════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
    ║ Prompt:
    ╟─────────────────────────────────────────────────────────────────────────────────────────────────────────────╢
    │      system: You are an expert story ideator. Only answer in a single sentence.
    │
    │        user: Generate a story idea about a dog.
    ╟─────────────────────────────────────────────────────────────────────────────────────────────────────────────╢
    ║ Output[0 of 4]:
    ╟─────────────────────────────────────────────────────────────────────────────────────────────────────────────╢
    │   assistant: A rescue dog with the ability to sense emotions helps a grieving child heal after the
    │              loss of a loved one, leading them both on a journey of friendship and discovery.
    ╚═════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
    Traceback (most recent call last):
    File "d:\\dev\\ell\\examples\\multilmp.py", line 53, in <module>
        story = write_a_really_good_story("a dog")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\decorators.py", line 207, in wrapper
        else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs, )
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\decorators.py", line 150, in wrapper
        res = fn(*fn_args, **fn_kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^
    File "d:\\dev\\ell\\examples\\multilmp.py", line 32, in write_a_really_good_story
        ideas = generate_story_ideas(about, api_params=(dict(n=4)))
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\decorators.py", line 216, in wrapper
        fn_closure, _uses = ell.util.closure.lexically_closured_source(func_to_track)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\util\\closure.py", line 306, in lexically_closured_source
        _, fnclosure, uses = lexical_closure(func, initial_call=True)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\util\\closure.py", line 250, in lexical_closure
        dep, _,  dep_uses = lexical_closure(
                            ^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\util\\closure.py", line 196, in lexical_closure
        ret = lexical_closure(
            ^^^^^^^^^^^^^^^^
    File "D:\\dev\\ell\\ell\\src\\ell\\util\\closure.py", line 140, in lexical_closure
        source = getsource(func, lstrip=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\anaconda\\envs\\ell_lab\\Lib\\site-packages\\dill\\source.py", line 374, in getsource
        lines, lnum = getsourcelines(object, enclosing=enclosing)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\anaconda\\envs\\ell_lab\\Lib\\site-packages\\dill\\source.py", line 345, in getsourcelines
        code, n = getblocks(object, lstrip=lstrip, enclosing=enclosing, locate=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\\anaconda\\envs\\ell_lab\\Lib\\site-packages\\dill\\source.py", line 271, in getblocks
        lines, lnum = findsource(object)
                    ^^^^^^^^^^^^^^^^^^
    File "D:\\anaconda\\envs\\ell_lab\\Lib\\site-packages\\dill\\source.py", line 215, in findsource
        line = lines[lnum]
            ~~~~~^^^^^^
    IndexError: list index out of range
    """

    # error_console_output = input("Enter the console output of the error. ").strip()
    if error_console_output is None or error_console_output == "":
        raise ValueError("Error console output is required. Please provide the console output of the error.")


    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop_path, "git_issue.md")

    # generate a conda yaml file. Add print for success and filepath.
    # env_info =  'generate a .yaml on desktop for the current conda environment. Add print for success and filepath.'
    # exec(generate_python_code_for_A_output_B(env_info))

    with open(output_file, "w") as f:
        f.write(generate_issue(error_console_output))

