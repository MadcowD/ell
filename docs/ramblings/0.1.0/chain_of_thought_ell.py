import ell

@ell.simple()
def chain_of_thought(question: str) -> str:
    return f"Reasoning: Let's think step by step in order to "



# DSP is basically sayyhing , dont prompt at all we have high level meta technqiues whic hhave a solution shape (neural architecture)

# we the n can train the promopts based on the solution shape

# in practice i migth actually not do shit liek that at all like inside ghost it was like



@ell.simple(model="gpt-4o")
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}" 

@ell.simple(model="gpt-4o")
def come_up_with_hook_subject_line(approaches, linkedinprofile):
    """ You are a helpful assistant that generates hook subject lines for emails based on approaches to emailing someone and their linkedin profile. """

    return f"Come up with a hook subject line for: {approaches} given that I am {linkedinprofile}"

@ell.simple(model="gpt-4o")
def write_email(hook_subject_line, linkedinprofile, aboutme):
    return f"Write an email based on the hook subject line: {hook_subject_line} and the approaches: {approaches}"


linkedinprofile = "linkedinprofile"
aboutme = "aboutme"

# people are used to doing shit like

approaches = generate_approaches_to_eamil_somone(linkedinprofile, aboutme)
hook_subject_line = come_up_with_hook_subject_line(approaches, linkedinprofile)
email = write_email(hook_subject_line, linkedinprofile, aboutme)


# what if we want to optimize this chain, or one dividiual prompt

optimizer = ell.FewShotFromLabels()
better_email_generator =  optimizer.fit(generate_approaches_to_eamil_somone, X=profiles, y=correct_appraoches)

fit: some_lmp -> a_new_lmp

# an lmp is a function that takes an input and returns the output of an lm. 
# when u FewShotFromLabels you prepend shit into the system prompt


# so this type of optimizaiton would happen after production of the prompt..
# it could serialize as
```python
def generate_approaches_to_eamil_somone(linkedinprofile, aboutme):
    """ You are a helpful assistant that generates approaches to email someone based on their linkedin profile and your about me. """

    return f"Come up with one for: {linkedinprofile} given that I am {aboutme}" 

@ell.simple(model="gpt-4o")
def better_email_generator(linkedinprofile, aboutme):
    message = generate_approaches_to_eamil_somone(linkedinprofile, aboutme)
    "prepend stuff to the messages!"
    return message
```
# So it could be that we want to preserve hte programmatic structure of the code... so that inputs are processed in as imilar way. But also we want to allow for variation in the prompt program string so its a double edged sword.



# like take a complicated lmp


# Actually if we introduce a new technique for optimizing LMPs then it doesnt matter..


#also what if we want to encourage people to use chain of thought.





    
    