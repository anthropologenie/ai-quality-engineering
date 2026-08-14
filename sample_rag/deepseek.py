"""The single sanctioned provider boundary — DeepSeek chat completions.

Sprint M2.06: the one external interaction `docs/GENERATION_CONTRACT.md` §24.3
permits under Repository Owner ruling **RO-13**, which transitions **G-14**
from *"no network I/O"* to *"**exactly one sanctioned external provider
interaction**, at the generation boundary"*.

§24.3 states the shape of that permission in the words this module is built to
respect: it is *"deliberately narrow, and is a permission for one call — not a
category of access."* Everything below exists to keep it that way.

Why this module exists separately from `sample_rag/model_generator.py`
------------------------------------------------------------------------
RO-13 (`docs/DEFERRED_ITEMS_REGISTER.md` §4.5 Decision 4) authorizes the
provider integration *"in one generation/provider module or the smallest
equivalent boundary"*. Two modules rather than one is the **smaller** boundary,
and deliberately so: **this file is the only module in `sample_rag/` that
imports a network primitive at all.** `model_generator.py` — the module that
implements the Generation Contract — imports `urllib` nowhere, opens no socket,
holds no endpoint and knows no credential, so the claim *"the Generator cannot
reach the network except through the one sanctioned call"* is a structural
property of the package rather than a promise about a function body.
`tests/test_model_generator.py` asserts both halves.

The provider contract is external and was verified, not remembered
-------------------------------------------------------------------
Every constant below was read from DeepSeek's published API documentation
during Sprint M2.06 and is recorded in `docs/M2.06_Generation_Report.md`
together with the source consulted. **None of it was inferred from memory** —
the endpoint, the authentication scheme, the request field set, the response
shape and the documented status codes are an external party's contract, and a
remembered version of someone else's contract is a guess wearing a fact's
clothes.

The dependency that was authorized and not taken
--------------------------------------------------
RO-13 authorizes a **third A-5 dependency exception** — one LLM/provider
integration library, for M2-06 only. **This module takes none.** `requirements.txt`
is unchanged and the repository remains a two-exception repository
(`sentence-transformers`, `faiss-cpu`).

The reasoning is the repository's own, applied unchanged. `docs/architecture.md`
§10 records *"minimal dependencies"* as a binding decision, and
`tests/test_lexical_bm25.py::test_m203_no_bm25_dependency_was_added` already
enforced it against a formula the repository could state in six lines. The two
exceptions that *were* taken were taken because the **algorithm** was the
dependency — a transformer checkpoint and an ANN index are not things to
hand-roll. An HTTP POST carrying a JSON document is not in that category:
`urllib.request` and `json` are the whole of it, both standard library, and an
SDK here would add a dependency tree for a request this file states in full.

Taking the exception remains available to a later sprint should the provider
contract outgrow this. **It is authorized; it is simply not needed yet**, and
recording that is more useful than spending it.

Credential handling
--------------------
`DEEPSEEK_API_KEY` is read from the process environment at the moment of the
call and **is never stored, returned, logged, printed, hashed, serialized, or
placed in an exception message**. It is not held on the client instance, so an
instance that escapes into a test fixture, a repr or a traceback carries no
secret. Every exception this module raises is constructed from a fixed reason
table and the request's own non-secret parameters; no provider response body and
no request header reaches an error string.

Determinism, and its exact boundary (§24.3)
--------------------------------------------
`build_request_body` and `parse_completion` are **pure functions of their
arguments** — same arguments, byte-identical request document and identical
parse result, every time. Error classification is a lookup in a fixed table.
That is the whole of the **structural determinism** half §24.3 keeps normative.

The `content` the provider returns is the other half, and **no determinism is
claimed for it**. §24.3: *"Repeated identical requests producing identical
responses is request reproducibility, and does not establish model-output
determinism."* `TEMPERATURE` below is a request parameter, not a guarantee.
"""

import json
import os
import urllib.error
import urllib.request

# The provider contract, as published. See the module docstring on why these are
# read from documentation rather than recalled, and
# `docs/M2.06_Generation_Report.md` for the source consulted at M2.06.
API_BASE_URL = "https://api.deepseek.com"
CHAT_COMPLETIONS_PATH = "/chat/completions"

# The credential's environment variable. The **name** is repository knowledge and
# belongs in source; the **value** is a secret and appears nowhere in tracked
# content, in any report, in any fixture, or in any error message.
API_KEY_VARIABLE = "DEEPSEEK_API_KEY"

# Engineering decision — the selected model. Both published models share a 1M
# context window and a 384K maximum output, so the choice is not a capability
# one; `flash` is the smaller of the two, and M2-06 answers a single grounded
# question over an assembled context measured in thousands of characters
# (`docs/M2.06_Generation_Stop_Report.md` §4.8). Selecting the larger model
# would be paying for headroom this capability does not use, and **no claim is
# made here about which produces better answers** — that is an evaluation
# question, and evaluation is M2-07 / M2-08.
DEFAULT_MODEL = "deepseek-v4-flash"

# Engineering decision — thinking mode disabled. The provider enables it by
# default and returns its trace as a separate `reasoning_content` field. This
# module maps `content` and nothing else, so leaving the trace enabled would
# spend latency and output budget on a value the Generation Contract has no
# field for. §24.4's bar on `GenerationResult` gaining new fields is why there
# is nowhere for it to go, and inventing somewhere would be this sprint
# amending an artifact RO-13 left unchanged.
THINKING = {"type": "disabled"}

# Engineering decision, and **not a determinism claim** (§24.3). A grounded
# question over supplied evidence is an extraction task, and the provider's
# default sampling temperature of 1 is tuned for open generation. `0` is the
# request parameter appropriate to the task. RO-13 *"establishes no such
# guarantee"* about provider-side deterministic sampling and *"no sprint may
# claim one from repeated calls alone"* — so this value is chosen for answer
# quality on an extraction task, and `answer_text` remains outside the
# structural-determinism half of G-9 regardless of it.
TEMPERATURE = 0

# Streaming is explicitly declined rather than left to the provider's default.
# This module parses one complete JSON document; a server-sent-event stream is a
# different response contract, and stating which one is being requested is what
# keeps `parse_completion` a total function of a documented shape.
STREAM = False

# A bounded wait, so a provider that never answers fails as a provider failure
# rather than hanging a caller indefinitely. Seconds.
REQUEST_TIMEOUT_SECONDS = 120

# The documented status codes, mapped to fixed reasons. A **table, not a
# heuristic**: §24.3 requires error classification to remain deterministic, and
# a classifier that parsed provider prose would vary with the provider's
# wording. An undocumented status is classified as a provider failure too — it
# is simply not one this table can name.
STATUS_REASONS = {
    400: "invalid request format",
    401: "authentication failed",
    402: "insufficient balance",
    422: "invalid request parameters",
    429: "rate limit reached",
    500: "provider server error",
    503: "provider overloaded",
}


class ProviderError(Exception):
    """Base for every failure at the sanctioned provider boundary.

    Named and module-level, following `ChunkConstructionError`,
    `DocumentConstructionError`, `VectorIndexCompatibilityError` and
    `ContextAssemblyError` — the repository's existing convention for a failure
    a caller is expected to be able to distinguish.

    A base class with three subclasses rather than a framework: the three are
    the distinctions a caller acts on differently, and each is a failure a
    `GenerationResult` must never be constructed from. **No provider failure of
    any kind is representable as a successful result** — the caller receives an
    exception or an artifact, never a degraded artifact standing in for one.
    """


class ProviderConfigurationError(ProviderError):
    """The call could not be attempted — the repository's own configuration.

    Raised before any network access, and distinct from a provider failure for
    a reason that matters operationally: a missing credential is fixed by the
    operator, a 503 is fixed by waiting. Collapsing the two would make an
    unconfigured repository look like an unavailable provider.
    """


class ProviderRequestError(ProviderError):
    """The provider was reached, or attempted, and the call did not succeed.

    Covers the documented status codes, undocumented ones, transport failures
    and timeouts. Carries a classified reason from `STATUS_REASONS` and never a
    response body, so the message cannot vary with provider wording and cannot
    carry anything the provider chose to echo.
    """


class ProviderResponseError(ProviderError):
    """The provider answered, and the answer was not the documented shape.

    Its own class deliberately. A malformed response is not a transport failure
    and is emphatically **not** a valid answer: §24.3's structural determinism
    covers *"response parsing"* and *"schema mapping"*, so a response missing
    `choices`, `message` or `content` fails here rather than becoming an empty
    or partial `answer_text` downstream.
    """


def build_request_body(messages: list, model: str = DEFAULT_MODEL) -> dict:
    """Construct the chat-completion request document — pure, and deterministic.

    A total function of `messages` and `model`: no clock, no environment, no
    random value, no measured duration and no set or dict iteration order
    participates, so the same arguments produce a byte-identical serialization
    every time. That is §24.3's *"request construction"* and *"provider request
    shape"*, both of which v2.0.0 keeps normative.

    **Exactly five fields, each a documented request parameter.** No tool
    declaration, no `tool_choice`, no `response_format`, no `stop`, no
    `logprobs`, no `user_id`, no `max_tokens`: the provider's own defaults are
    correct for a single grounded answer, and each field added here would be a
    request-shaping decision no repository authority asked for. Tool calling and
    model routing are barred outright by §24.3's G-14 transition.

    The credential is **not** part of the body and never appears in one — it is
    a transport header, applied in `complete`, and this function can therefore
    be exercised, printed and compared in a specification without any secret
    being reachable from it.
    """
    return {
        "model": model,
        "messages": messages,
        "stream": STREAM,
        "temperature": TEMPERATURE,
        "thinking": THINKING,
    }


def parse_completion(payload: dict) -> str:
    """Extract the assistant's answer text from a response document — pure.

    §24.3 keeps *"response parsing"* and *"schema mapping"* deterministic, so
    this reads exactly the documented path and nothing adjacent to it:

        payload["choices"][0]["message"]["content"]

    **Every departure from that shape is `ProviderResponseError`**, including a
    `content` that is present but empty or not a string. That strictness is what
    `docs/GENERATION_CONTRACT.md` G-3 rests on downstream — *"`answer_text` SHALL
    be a non-empty string on every path"* — and it is why no default, no
    fallback field and no empty-string substitution appears below. A malformed
    response that quietly became `""` would satisfy the type and violate the
    guarantee.

    `reasoning_content`, `tool_calls`, `usage`, `logprobs`, `system_fingerprint`
    and every other documented field are deliberately not read. The Generation
    Contract has no field for any of them (§24.4 authorizes no new
    `GenerationResult` field), so reading one would produce a value with nowhere
    to go.
    """
    if not isinstance(payload, dict):
        raise ProviderResponseError("Provider response was not a JSON object.")

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderResponseError("Provider response carried no choices.")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ProviderResponseError("Provider response carried no message.")

    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise ProviderResponseError("Provider response carried no answer content.")

    return content


class DeepSeekClient:
    """One sanctioned provider interaction, and no other capability.

    Stateless with respect to secrets: the credential is read from the
    environment inside `complete` and is never bound to the instance, so no
    attribute, `repr`, pickle or traceback frame holding this object can carry
    it.

    Holds no session, no connection pool, no retry policy, no backoff, no
    circuit breaker and no cache. Each is a reasonable thing for a production
    client to have and each would make this more than *"a permission for one
    call"*: a retry loop in particular turns one sanctioned interaction into an
    unbounded number of them, and the caller — not this module — is where a
    decision to try again belongs.

    **No model routing, no model selection logic, no fallback model.** The model
    is fixed at construction, and §24.3's G-14 transition bars routing by name.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = API_BASE_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ):
        """Bind the client to one model, one endpoint and one timeout.

        All three are parameters rather than constants read at the point of use,
        so a specification can pin the request this client would build without
        reaching the network — and so the endpoint appears in exactly one place.

        **No credential parameter exists**, deliberately. A client that accepted
        a key as an argument would invite one into a call site, a fixture, a
        default value or a log line; reading the environment inside `complete`
        keeps the only path to the secret one this module controls.
        """
        self._model = model
        self._base_url = base_url
        self._timeout = timeout

    @property
    def model(self) -> str:
        """The selected model identifier — safe to record as sprint evidence."""
        return self._model

    @property
    def endpoint(self) -> str:
        """The full chat-completions URL. Carries no credential."""
        return f"{self._base_url}{CHAT_COMPLETIONS_PATH}"

    def complete(self, messages: list) -> str:
        """Perform the one sanctioned provider interaction and return its text.

        The whole of G-14's permission, in one method: build a request, send it
        once, parse the answer. **One call, no retry**, and no path through this
        method reaches a second one.

        Failures are classified, never swallowed and never softened into a
        result:

        | Condition | Raised |
        |---|---|
        | credential absent or blank | `ProviderConfigurationError` |
        | documented or undocumented HTTP status | `ProviderRequestError` |
        | timeout, DNS or transport failure | `ProviderRequestError` |
        | response body is not JSON | `ProviderResponseError` |
        | response is JSON of the wrong shape | `ProviderResponseError` |

        **No exception below carries the credential, a request header, or a
        response body.** Each message is assembled from this module's own fixed
        vocabulary and the request's non-secret parameters, and the underlying
        exception is suppressed with `from None` so no chained `urllib` object
        travels with it.

        Reads the environment; writes nothing, anywhere. No filesystem I/O — the
        one thing §24.3 leaves *"barred outright"* after the G-14 transition.
        """
        api_key = os.environ.get(API_KEY_VARIABLE)
        if not api_key:
            raise ProviderConfigurationError(
                f"{API_KEY_VARIABLE} is not set in the environment. Generation "
                f"requires the provider credential and does not fall back to a "
                f"stub, a cached answer or an unevidenced result."
            )

        body = json.dumps(build_request_body(messages, self._model)).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            reason = STATUS_REASONS.get(error.code, "unexpected provider status")
            raise ProviderRequestError(
                f"DeepSeek returned HTTP {error.code} ({reason}) for model "
                f"{self._model!r}."
            ) from None
        except urllib.error.URLError:
            raise ProviderRequestError(
                f"DeepSeek could not be reached within {self._timeout}s for "
                f"model {self._model!r}."
            ) from None
        except (TimeoutError, OSError):
            raise ProviderRequestError(
                f"The DeepSeek request failed in transport within "
                f"{self._timeout}s for model {self._model!r}."
            ) from None
        except json.JSONDecodeError:
            raise ProviderResponseError(
                "Provider response was not valid JSON."
            ) from None

        return parse_completion(payload)
