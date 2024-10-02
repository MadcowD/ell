import ell


ell.init(verbose=True)

@ell.complex("gpt-4o-audio-preview")
def test():
    return [ell.user("Hey! Could you talk to me in spanish? I'd like to hear how you say 'ell'.")]

response = test()
print(response.audios[0])

if __name__ == "__main__":
    test()

