# Website demo recording package

This package contains a verified page-by-page screenshot set plus a real-browser interactive demo recording.

- [`CD4_portal_demo_3min_silent.mp4`](CD4_portal_demo_3min_silent.mp4) is the 2:53, 1280 × 720 silent walkthrough captured from the live local site.
- `STORYBOARD.md` documents the interactive cut and its browser actions.
- `VIDEO_VOICEOVER.md` is the narration timed to the finished video.
- `SCRIPT.md` provides a page-by-page Traditional Chinese introduction and explains why every screen matters.
- `screenshots/` contains 16 Playwright **full-page** captures at 1920 px width; image height follows the complete page content.

The walkthrough shows real navigation, weight controls, gene search, the PLCG1 dossier, Core-5 comparison, interactive figures, and the figure gallery. Its final 30 seconds open A7, A12, and A16 full-size for dedicated explanation.

The plan combines two existing repo drafts:

- `docs/mvp-research/pipeline/blindspot_fixes/USER_TEST_SCRIPT.md` supplies the researcher and clinical-evidence user journeys.
- `frontend/webserver/src/views/Deck.tsx` supplies the project-level story: scale, guardrails, preliminary outputs, and provenance.

## Recording guardrails

- Say “research-use target prioritisation” rather than “clinical recommendation.”
- Keep the two funnels parallel: the portal readiness path ends at 302 advance-ready targets; the publication delivery-decision path ends at 39 targets with a known modality.
- Define Core-5 as the intersection of the independent 15-gene primary-outcome shortlist and the publication set of 39.
- Describe the individual expression comparison as local, de-identified, and hypothesis-generating. It is not diagnosis, treatment selection, or efficacy prediction.
- Treat concept-module membership as descriptive. It never feeds the readiness call.

## Using your own voice

Playwright records the browser video but does not capture microphone audio. Record `VIDEO_VOICEOVER.md` separately with OBS, Audacity, Voice Memos, or another recorder, then combine it with the supplied silent MP4. The script is divided into short timed blocks so each paragraph can be recorded as a separate take.

Recommended workflow:

1. Play `CD4_portal_demo_3min_silent.mp4` while recording your voice.
2. Read `VIDEO_VOICEOVER.md` into a microphone as separate timed clips.
3. Remove long breaths and background noise, but keep the natural voice.
4. Merge the tracks with an editor, or with FFmpeg:

   ```bash
   ffmpeg -i CD4_portal_demo_3min_silent.mp4 -i narration.wav -c:v copy -c:a aac -b:a 192k -shortest CD4_portal_demo_with_voice.mp4
   ```

## Screenshot index

1. [Home](screenshots/01-home.png)
2. [Target Explorer](screenshots/02-target-explorer.png)
3. [PLCG1 target dossier](screenshots/03-target-dossier-plcg1.png)
4. [Core-5 comparison](screenshots/04-core5-compare.png)
5. [Clinical scope and guardrails](screenshots/05-clinical-scope.png)
6. [Clinical Core-5 evidence matrix](screenshots/06-clinical-core5.png)
7. [Individual concept profile](screenshots/07-clinical-concept.png)
8. [Disease × drug evidence](screenshots/08-clinical-disease-drug.png)
9. [Population genetics](screenshots/09-clinical-popgen.png)
10. [Expression-feature comparison result](screenshots/10-clinical-expression-compare.png)
11. [Interactive figures](screenshots/11-interactive-figures.png)
12. [Figure and structure gallery](screenshots/12-figure-gallery.png)
13. [Docs and references](screenshots/13-docs.png)
14. [REST API](screenshots/14-api-docs.png)
15. [Four-slide overview](screenshots/15-overview-deck.png)
16. [Provenance](screenshots/16-provenance.png)
