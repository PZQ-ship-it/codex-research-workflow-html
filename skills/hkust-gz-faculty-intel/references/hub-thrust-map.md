# HKUST(GZ) Hub and Thrust Map

The crawler embeds the public Hub/Thrust map extracted from the HKUST(GZ) Faculty Profile frontend.

## Main Hubs

| Hub | Key | Thrust | Code |
|---|---|---|---|
| Function Hub | `FUNCHUB` | Advanced Materials | `10011A10000000000H1Y` |
| Function Hub | `FUNCHUB` | Earth, Ocean and Atmospheric Sciences | `10011A10000000000H20` |
| Function Hub | `FUNCHUB` | Microelectronics | `10011A10000000000H22` |
| Function Hub | `FUNCHUB` | Sustainable Energy and Environment | `10011A10000000000H24` |
| Information Hub | `INFOHUB` | Artificial Intelligence | `10011A10000000000H28` |
| Information Hub | `INFOHUB` | Computational Media and Arts | `10011A10000000000H2A` |
| Information Hub | `INFOHUB` | Data Science and Analytics | `10011A10000000000H2C` |
| Information Hub | `INFOHUB` | Internet of Things | `10011A10000000000H2E` |
| Systems Hub | `SYSTHUB` | Bioscience and Biomedical Engineering | `10011A10000000000H2I` |
| Systems Hub | `SYSTHUB` | Intelligent Transportation | `10011A10000000000H2K` |
| Systems Hub | `SYSTHUB` | Robotics and Autonomous Systems | `10011A10000000000H2M` |
| Systems Hub | `SYSTHUB` | Smart Manufacturing | `10011A10000000000H2O` |
| Society Hub | `SOCIHUB` | Carbon Neutrality and Climate Change | `10011A100000000259HQ` |
| Society Hub | `SOCIHUB` | Financial Technology | `10011A10000000000H2S` |
| Society Hub | `SOCIHUB` | Innovation, Policy and Entrepreneurship | `10011A10000000000H2U` |
| Society Hub | `SOCIHUB` | Urban Governance and Design | `10011A10000000000H2Y` |

## Accepted Name Forms

The script resolves Hub and Thrust names case-insensitively and ignores punctuation, spaces, `&`, and hyphens. These all work:

- `Information Hub`
- `INFOHUB`
- `information`
- `Artificial Intelligence`
- `Artificial-Intelligence`
- `ai` is not a built-in alias; use the full name or official code for ambiguous abbreviations.

## Direct URL Mode

For URLs shaped like:

```text
https://facultyprofiles.hkust-gz.edu.cn/thrust-faculties?code=10011A10000000000H28
```

the crawler extracts `code` and resolves the matching Hub/Thrust from the embedded map.
