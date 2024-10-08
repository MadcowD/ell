import ell2a


ell2a.init(verbose=True)

@ell2a.complex("gpt-4o-audio-preview")
def test():
    return [ell2a.user("Hey! Could you talk to me in spanish? I'd like to hear how you say 'ell2a'.")]

response = test()
print(response.audios[0])

if __name__ == "__main__":
    test()

