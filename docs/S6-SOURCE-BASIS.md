# S6 source-basis correction

12 October 2026. This corrects the prerequisite stated in
[ISO readback](S6-ISO-READBACK.md) and [source-contract calibration](S6-SOURCE-CONTRACTS.md).
Those retained reports and failed declarations remain unchanged. **S6 is incomplete.**

Obtaining a full ISO publication is not a mandatory runtime or study gate.
The necessary evidence is a defensible interpretation of the original promise,
independently derived expectations and properly adjudicated controls. Public
sources can establish that interpretation; possessing the standard cannot by
itself establish implementation correctness or verifier trustworthiness.

The [NASA overview](https://science.data.nasa.gov/fits/documentation/iso-time)
describes calendar, ordinal and week dates, basic/extended time representations,
reduced time precision, offsets and midnight rollover.
[IERS Bulletin C 52](https://datacenter.iers.org/data/16/bulletinc-052.txt)
establishes the actual 2016 leap second. The available
[final 2022 amendment](https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf)
explicitly covers decimal hour/minute/second fractions and restores end-of-day
representation. The published 2019 preview confirms leap-second representation.
These sources already support repairing the known UTC defects.

The [2016 working draft](https://www.loc.gov/standards/datetime/iso-tc154-wg5_n0038_iso_wd_8601-1_2016-02-16.pdf)
is additional technical context, with its draft status retained. It must not be
called the final standard. [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339)
provides public offset/leap-second discussion and an informational collected ISO
grammar in Appendix A; that appendix explicitly warns about its older edition
and possible errors. RFC 3339's normative timestamp format is a narrower profile
and must not replace the original ISO promise.

The UTC artifact remains unresolved because corrected positive controls have not
been independently validated, rather than because a particular PDF is unavailable.
No source requirement, acceptance threshold, missing-evidence rule or native trust
gate was relaxed. The new gap wording does not constitute a verification remedy
or a successful qualification. Existing frozen campaigns cannot resume under
changed runtime files. Repair and independently adjudicate controls, freeze a new
qualification, retain every outcome, and unlock comparisons only if it passes.
