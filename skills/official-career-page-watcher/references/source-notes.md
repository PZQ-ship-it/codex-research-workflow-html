# Source Notes

Updated: 2026-06-30

These seeds were initialized from AnySearch discovery plus official domain inspection during the HKUST(GZ) RA career-value workflow. The watcher is a monitoring aid, not a source ledger for salary facts.

## Initial AnySearch Discovery

| Group | Useful Official Entrypoints Found | Notes |
|---|---|---|
| Tencent | `careers.tencent.com`, `join.qq.com` | Tencent search pages surfaced 混元 roles and Shenzhen/Guangzhou hints in snippets. |
| Huawei | `career.huawei.com`, `huaweicloud.com/lab/algorithm/postdoctoral_recruitment.html` | Official social, campus, postdoc, and Huawei Cloud algorithm postdoc pages were visible. |
| ByteDance | `jobs.bytedance.com`, `seed.bytedance.com` | Seed career, Seed early-career, and Top Seed pages are the strongest AI/PhD-related official anchors. |
| Alibaba | `talent.alibaba.com`, `careers-tongyi.alibaba.com`, `joindamo.alibaba.com`, `careers.aliyun.com` | Tongyi / DAMO / Aliyun pages provide more direction-specific anchors than the group home alone. |
| Baidu | `talent.baidu.com` | Search snippets surfaced 2027AIDU 大模型 roles with Beijing/Shenzhen. |
| Meituan | `campus.meituan.com`, `zhaopin.meituan.com` | LongCat, Agent, RAG, and multimodal snippets were visible in official job lists. |
| Kuaishou | `zhaopin.kuaishou.cn` | Official platform found, but many role-specific signals came from secondary sources. |
| Xiaomi | `hr.xiaomi.com`, `campus.hr.xiaomi.com`, `mimo.xiaomi.com` | MiMo pages add a more specific reasoning / knowledge-engineering signal. |
| SenseTime | `sensetime.com/cn/join-us`, `hr.sensetime.com` | Official pages are often JS-heavy; watcher output may need browser follow-up. |
| Peng Cheng Laboratory | `hr.pcl.ac.cn` | Official lab recruitment home and social recruitment page. |
| IDEA | `idea.edu.cn`, `idea.zhiye.com` | Official institute page and recruitment system. |
| Guangming Laboratory | `gml.ac.cn` | Official lab page includes recruitment entry points. |
| HKGAI / HKUST | `hkgai.info`, `hkustcareers.hkust.edu.hk` | Hong Kong generative AI center and HKUST careers postdoc detail. |
| AIRS / CUHK-Shenzhen | `cuhk.edu.cn/zh-hans/recruitment/14638` | Official CUHK-Shenzhen recruitment announcement for AIRS. |
| Shenzhen University of Advanced Technology | `rczpw.suat-sz.edu.cn` | Official 大模型研究中心 recruitment announcement. |

## Evidence Policy

- Watcher outputs support "this official page changed" or "this official page currently exposes keywords through a simple public fetch".
- They do not support salary or offer conclusions without direct JD inspection and cross-source synthesis.
- If a page is JS-only or blocked under simple fetch, use Playwright/browser/manual inspection and record only safe metadata in downstream ledgers.
