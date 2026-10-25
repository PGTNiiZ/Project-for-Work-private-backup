from common.scrub import patterns, scrub

L, H = "octocat", "alice.bsky.social"


def tgt(text):
    return scrub(text, patterns(L, H, "target"))


def gh(text):
    return scrub(text, patterns(L, H, "github"))


def test_github_refs_on_target_side():
    for text, name in [
        ("see https://GitHub.com/OctoCat for code", "github_url"),
        ("octocat.github.io", "github_io"),
        ("GH: octocat", "gh_prefix"),
        ("gh:octocat", "gh_prefix"),
        ("github : @octocat", "github_prefix"),
        ("I am @octocat on GitHub", "at_login_on_github"),
    ]:
        out, hit = tgt(text)
        assert name in hit, text
        assert "octocat" not in out.lower(), text


def test_bluesky_refs_on_github_side():
    for text, name in [
        ("https://bsky.app/profile/alice.bsky.social", "bsky_url"),
        ("@alice.bsky.social", "at_handle"),
        ("find me: Alice.Bsky.Social", "bare_handle"),
    ]:
        out, hit = gh(text)
        assert name in hit, text
        assert "alice" not in out.lower(), text


def test_zero_width_and_lookalikes():
    out, hit = tgt("g​ithub.com/octo‍cat")
    assert hit and "octocat" not in out
    out, hit = tgt("gitһub.com/оctocat")  # Cyrillic һ and о
    assert hit and "ctocat" not in out
    out, hit = tgt("ｇｉｔｈｕｂ.ｃｏｍ/octocat")  # fullwidth
    assert hit


def test_no_false_positive_and_text_kept():
    out, hit = tgt("github.com/octocat2 and octocatfan")
    assert not hit and out == "github.com/octocat2 and octocatfan"
    out, hit = tgt("Python dev. GH: octocat. Coffee!")
    assert out == "Python dev. . Coffee!"
