# Gemini Input 合成：enum 坍缩与可疑样本审计

> 这是分布风险标记，不是自动删除名单。固定话术或有限分类场景出现重复 Answer 可能是正确行为；标记表示在放量或训练前需要结合 Requirements 复核。

## 快照

- 审计时间：`2026-08-15T01:56:54+08:00`
- 输入目录：`/Users/liyong90/Desktop/sop-maze/answer_first_input_synthesis_20260813/runs/gemini_all_1`
- 快照编号文件：8877
- 可审计的 `candidate/ok`：6472
- 出现可疑标记的场景：83 / 131
- 被标记的样本：499
- 状态分布：`{"candidate": 6472, "input_error": 72, "target_error": 2303, "target_ready": 30}`

本报告只读源文件，没有修改任何样本。生成过程仍在运行时，后来创建或改写的记录不属于本次快照。

## 刚刚发现的问题

当前 Answer 规划器先从 Output JSON Schema 的 enum 字段采样软目标，再让模型补齐完整 `target_answer`。这个办法可以改善离散分支覆盖，但不能自动保证自由文本、数值、数组长度和业务对象也多样。模型可能反复采用同一组默认值或最常见模板，只轮换一个 enum，形成“Schema 合法但 Answer 分布坍缩”。

`050_meituan_03_酒店旅游_v28` 是直观例子：`住[].早餐.含早与否` 的“含早/不含早”确实是 enum；但房型、景观、设施、餐饮和随住服务中的许多字段不是 enum。只采样早餐 enum，不能防止其余字段反复出现 `null`、0 或同一房型。

根因不是 JSON Schema 校验失败，而是 **Schema 合法性门只检查单条记录，无法检查批次分布**。此外，部分业务组合不可达时模型会把软目标最小修正回常见分支，也可能造成 anchor 未命中或结果集中。

## 标记口径

- `ANCHOR_MISMATCH`：记录中的 anchor enum 软目标没有被最终 `target_answer` 命中。这是最直接的分支覆盖失败信号。
- `DOMINANT_EXACT_ANSWER`：同场景中完全相同的 `target_answer` 大簇至少有5条，且达到有效样本的15%。
- `ENUM_ONLY_VARIATION`：屏蔽 Schema enum 值后，结构和非 enum 字段形成大簇；簇内仍有至少两个不同 Answer，说明差异主要来自 enum。
- `SCENE_LOW_UNIQUE_RATIO`：场景至少10条有效记录，但完整 `target_answer` 唯一率低于25%。

这些口径偏向召回风险。尤其固定 Step/固定话术任务可能被 `DOMINANT_EXACT_ANSWER` 或 `SCENE_LOW_UNIQUE_RATIO` 标记，但不应在没有业务复核时删除。

## 全局标记统计

| 标记 | 样本数 |
|---|---:|
| `ANCHOR_MISMATCH` — enum anchor 未命中（强可疑） | 394 |
| `DOMINANT_EXACT_ANSWER` — 完全相同 target_answer 形成大簇 | 66 |
| `ENUM_ONLY_VARIATION` — 除 enum 外的结构/自由字段相同 | 101 |
| `SCENE_LOW_UNIQUE_RATIO` — 场景 target_answer 唯一率低于25% | 0 |

## 可疑场景汇总

| 场景 | 有效样本 | Answer唯一数/比例 | 最大完全重复簇 | enum屏蔽后唯一数/最大簇 | 可疑样本 |
|---|---:|---:|---:|---:|---:|
| `075_payment_06_支付风控解冻_v28` | 54 | 30 / 55.6% | 4 / 7.4% | 8 / 23 | 44 |
| `069_meituan_24_美团直播_v28` | 50 | 19 / 38.0% | 8 / 16.0% | 18 / 8 | 30 |
| `081_pdd_07_多多直播_v28` | 50 | 36 / 72.0% | 3 / 6.0% | 16 / 15 | 25 |
| `019_eleme_10_饿了么物流管理_v28` | 50 | 33 / 66.0% | 11 / 22.0% | 25 / 22 | 24 |
| `128_08_coworking_room` | 49 | 49 / 100.0% | 1 / 2.0% | 49 / 1 | 20 |
| `121_01_smart_locker` | 45 | 45 / 100.0% | 1 / 2.2% | 45 / 1 | 18 |
| `028_insurance_05_保险客户投诉处理_v28` | 52 | 37 / 71.2% | 16 / 30.8% | 37 / 16 | 16 |
| `124_04_parking_pass` | 46 | 46 / 100.0% | 1 / 2.2% | 46 / 1 | 16 |
| `006_bank_06_投诉建议处理_v28` | 49 | 36 / 73.5% | 14 / 28.6% | 36 / 14 | 15 |
| `126_06_fitness_class` | 52 | 52 / 100.0% | 1 / 1.9% | 52 / 1 | 15 |
| `129_09_lab_instrument` | 44 | 44 / 100.0% | 1 / 2.3% | 44 / 1 | 14 |
| `082_pdd_09_多多国际_v28` | 46 | 42 / 91.3% | 4 / 8.7% | 42 / 4 | 13 |
| `038_jingdong_07_订单信息修改_v28` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 12 |
| `125_05_ev_charging` | 47 | 47 / 100.0% | 1 / 2.1% | 47 / 1 | 12 |
| `130_10_cloud_printing` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 12 |
| `050_meituan_03_酒店旅游_v28` | 50 | 36 / 72.0% | 9 / 18.0% | 34 / 11 | 11 |
| `026_insurance_03_保单变更流程_v28` | 48 | 39 / 81.2% | 8 / 16.7% | 38 / 8 | 10 |
| `127_07_laundry_care` | 48 | 48 / 100.0% | 1 / 2.1% | 48 / 1 | 9 |
| `008_chain_restaurant_02_海底捞服务_v28` | 46 | 39 / 84.8% | 4 / 8.7% | 39 / 4 | 8 |
| `067_meituan_22_美团企业版_v28` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 8 |
| `123_03_public_library` | 43 | 43 / 100.0% | 1 / 2.3% | 43 / 1 | 8 |
| `131_01_delivery_progress` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 8 |
| `132_06_jingdong_invoice_reissue_v28` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 8 |
| `046_jingdong_16_企业购_v28` | 47 | 46 / 97.9% | 2 / 4.3% | 46 / 2 | 7 |
| `122_02_pet_clinic` | 49 | 49 / 100.0% | 1 / 2.0% | 49 / 1 | 7 |
| `001_bank_01_信用卡申请审批流程_v28` | 50 | 33 / 66.0% | 3 / 6.0% | 29 / 3 | 5 |
| `002_bank_02_挂失解挂流程_v28` | 50 | 49 / 98.0% | 2 / 4.0% | 49 / 2 | 5 |
| `009_chain_restaurant_03_星巴克门店运营_v28` | 48 | 47 / 97.9% | 2 / 4.2% | 47 / 2 | 5 |
| `088_pdd_20_多多爱消除_v28` | 51 | 46 / 90.2% | 3 / 5.9% | 46 / 3 | 5 |
| `092_taobao_08_discount_v28` | 47 | 45 / 95.7% | 3 / 6.4% | 45 / 3 | 5 |
| `117_08_document_destruction` | 53 | 34 / 64.2% | 4 / 7.5% | 33 / 4 | 5 |
| `118_09_corporate_headshot` | 46 | 32 / 69.6% | 4 / 8.7% | 31 / 5 | 5 |
| `093_taobao_10_千牛商家服务_v28` | 50 | 48 / 96.0% | 2 / 4.0% | 47 / 2 | 4 |
| `098_telecom_02_中国联通客服_v28` | 50 | 49 / 98.0% | 2 / 4.0% | 48 / 2 | 4 |
| `119_10_suit_measurement` | 49 | 35 / 71.4% | 3 / 6.1% | 35 / 3 | 4 |
| `015_eleme_06_饿了么会员_v28` | 48 | 48 / 100.0% | 1 / 2.1% | 47 / 2 | 3 |
| `017_eleme_08_饿了么企业版_v28` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 3 |
| `055_meituan_08_美团外卖运营_v28` | 53 | 49 / 92.5% | 5 / 9.4% | 49 / 5 | 3 |
| `063_meituan_15_美团闪购商家端_v28` | 48 | 47 / 97.9% | 2 / 4.2% | 46 / 3 | 3 |
| `068_meituan_23_美团金融_v28` | 47 | 29 / 61.7% | 3 / 6.4% | 29 / 3 | 3 |
| `086_pdd_17_多多批发_v28` | 51 | 39 / 76.5% | 2 / 3.9% | 38 / 2 | 3 |
| `099_telecom_03_中国电信客服_v28` | 53 | 51 / 96.2% | 3 / 5.7% | 51 / 3 | 3 |
| `102_03_city_museum_pass` | 51 | 30 / 58.8% | 3 / 5.9% | 29 / 3 | 3 |
| `110_01_piano_tuning` | 52 | 38 / 73.1% | 3 / 5.8% | 38 / 3 | 3 |
| `115_06_moveout_inspection` | 47 | 32 / 68.1% | 3 / 6.4% | 31 / 3 | 3 |
| `116_07_aging_in_place` | 48 | 31 / 64.6% | 4 / 8.3% | 30 / 4 | 3 |
| `003_bank_03_转账异常处理_v28` | 51 | 43 / 84.3% | 4 / 7.8% | 43 / 4 | 2 |
| `004_bank_04_贷款咨询与申请_v28` | 48 | 42 / 87.5% | 2 / 4.2% | 41 / 2 | 2 |
| `058_meituan_10_美团充电宝_v28` | 53 | 38 / 71.7% | 3 / 5.7% | 38 / 3 | 2 |
| `060_meituan_12_美团客服_v28` | 50 | 31 / 62.0% | 3 / 6.0% | 31 / 3 | 2 |
| `080_pdd_06_多多进宝_v28` | 54 | 29 / 53.7% | 4 / 7.4% | 28 / 4 | 2 |
| `084_pdd_13_砍价免费拿_v28` | 50 | 49 / 98.0% | 2 / 4.0% | 49 / 2 | 2 |
| `090_taobao_02_闲鱼二手交易_v28` | 53 | 51 / 96.2% | 3 / 5.7% | 51 / 3 | 2 |
| `103_04_fleet_maintenance` | 48 | 29 / 60.4% | 3 / 6.2% | 29 / 3 | 2 |
| `104_05_corporate_fitness_pass` | 47 | 31 / 66.0% | 3 / 6.4% | 31 / 3 | 2 |
| `108_09_it_asset_recovery` | 50 | 28 / 56.0% | 3 / 6.0% | 28 / 3 | 2 |
| `111_02_moving_estimate` | 51 | 36 / 70.6% | 4 / 7.8% | 36 / 4 | 2 |
| `114_05_pet_grooming` | 50 | 35 / 70.0% | 4 / 8.0% | 35 / 4 | 2 |
| `005_bank_05_理财产品购买流程_v28` | 49 | 43 / 87.8% | 2 / 4.1% | 41 / 2 | 1 |
| `012_eleme_02_饿了么商家端_v28` | 49 | 49 / 100.0% | 1 / 2.0% | 49 / 1 | 1 |
| `022_eleme_16_饿了么评价管理_v28` | 52 | 52 / 100.0% | 1 / 1.9% | 51 / 2 | 1 |
| `030_insurance_07_查勘定损流程_v28` | 48 | 47 / 97.9% | 2 / 4.2% | 47 / 2 | 1 |
| `032_insurance_12_反欺诈调查流程_v28` | 50 | 46 / 92.0% | 2 / 4.0% | 46 / 2 | 1 |
| `033_jingdong_01_七天无理由退货_v28` | 51 | 51 / 100.0% | 1 / 2.0% | 51 / 1 | 1 |
| `034_jingdong_02_商品质量问题退货_v28` | 50 | 38 / 76.0% | 2 / 4.0% | 38 / 2 | 1 |
| `036_jingdong_04_仅退款不退货_v28` | 48 | 37 / 77.1% | 2 / 4.2% | 37 / 2 | 1 |
| `037_jingdong_05_30天价保申请_v28` | 51 | 48 / 94.1% | 3 / 5.9% | 48 / 3 | 1 |
| `039_jingdong_08_物流异常处理_v28` | 50 | 47 / 94.0% | 2 / 4.0% | 47 / 2 | 1 |
| `045_jingdong_14_京东服务__v28` | 49 | 46 / 93.9% | 2 / 4.1% | 46 / 2 | 1 |
| `048_jingdong_18_交易纠纷仲裁_v28` | 51 | 47 / 92.2% | 2 / 3.9% | 47 / 2 | 1 |
| `049_meituan_01_外卖配送_v28` | 50 | 48 / 96.0% | 2 / 4.0% | 48 / 2 | 1 |
| `056_meituan_08_美团打车_v28` | 54 | 53 / 98.1% | 2 / 3.7% | 53 / 2 | 1 |
| `059_meituan_11_美团会员_v28` | 50 | 49 / 98.0% | 2 / 4.0% | 49 / 2 | 1 |
| `076_pdd_01_百亿补贴_v28` | 50 | 50 / 100.0% | 1 / 2.0% | 50 / 1 | 1 |
| `079_pdd_04_多多买菜_v28` | 52 | 52 / 100.0% | 1 / 1.9% | 52 / 1 | 1 |
| `083_pdd_10_假一赔十_v28` | 51 | 48 / 94.1% | 2 / 3.9% | 47 / 2 | 1 |
| `091_taobao_07_淘宝联盟推广_v28` | 50 | 34 / 68.0% | 3 / 6.0% | 31 / 4 | 1 |
| `094_taobao_12_campaign_v28` | 48 | 47 / 97.9% | 2 / 4.2% | 47 / 2 | 1 |
| `095_taobao_14_淘宝租赁_v28` | 47 | 45 / 95.7% | 2 / 4.3% | 45 / 2 | 1 |
| `100_01_reusable_container` | 47 | 29 / 61.7% | 3 / 6.4% | 28 / 3 | 1 |
| `105_06_corporate_dental_screening` | 51 | 31 / 60.8% | 3 / 5.9% | 31 / 3 | 1 |
| `112_03_air_sampling` | 52 | 34 / 65.4% | 3 / 5.8% | 34 / 3 | 1 |
| `113_04_office_plant_care` | 46 | 31 / 67.4% | 3 / 6.5% | 31 / 3 | 1 |

## 全部可疑样本

### `001_bank_01_信用卡申请审批流程_v28`

场景统计：有效=50，完整Answer唯一率=66.0%，最大完全重复簇=6.0%，可疑样本=5。

- ⚠ `001_bank_01_信用卡申请审批流程_v28/026.json` — enum anchor 未命中（强可疑）
- ⚠ `001_bank_01_信用卡申请审批流程_v28/027.json` — enum anchor 未命中（强可疑）
- ⚠ `001_bank_01_信用卡申请审批流程_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `001_bank_01_信用卡申请审批流程_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `001_bank_01_信用卡申请审批流程_v28/057.json` — enum anchor 未命中（强可疑）

### `002_bank_02_挂失解挂流程_v28`

场景统计：有效=50，完整Answer唯一率=98.0%，最大完全重复簇=4.0%，可疑样本=5。

- ⚠ `002_bank_02_挂失解挂流程_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `002_bank_02_挂失解挂流程_v28/015.json` — enum anchor 未命中（强可疑）
- ⚠ `002_bank_02_挂失解挂流程_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `002_bank_02_挂失解挂流程_v28/030.json` — enum anchor 未命中（强可疑）
- ⚠ `002_bank_02_挂失解挂流程_v28/043.json` — enum anchor 未命中（强可疑）

### `003_bank_03_转账异常处理_v28`

场景统计：有效=51，完整Answer唯一率=84.3%，最大完全重复簇=7.8%，可疑样本=2。

- ⚠ `003_bank_03_转账异常处理_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `003_bank_03_转账异常处理_v28/053.json` — enum anchor 未命中（强可疑）

### `004_bank_04_贷款咨询与申请_v28`

场景统计：有效=48，完整Answer唯一率=87.5%，最大完全重复簇=4.2%，可疑样本=2。

- ⚠ `004_bank_04_贷款咨询与申请_v28/003.json` — enum anchor 未命中（强可疑）
- ⚠ `004_bank_04_贷款咨询与申请_v28/039.json` — enum anchor 未命中（强可疑）

### `005_bank_05_理财产品购买流程_v28`

场景统计：有效=49，完整Answer唯一率=87.8%，最大完全重复簇=4.1%，可疑样本=1。

- ⚠ `005_bank_05_理财产品购买流程_v28/042.json` — enum anchor 未命中（强可疑）

### `006_bank_06_投诉建议处理_v28`

场景统计：有效=49，完整Answer唯一率=73.5%，最大完全重复簇=28.6%，可疑样本=15。

- ⚠ `006_bank_06_投诉建议处理_v28/001.json` — 完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/004.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/008.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/011.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/014.json` — 完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/016.json` — 完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/018.json` — enum anchor 未命中（强可疑）
- ⚠ `006_bank_06_投诉建议处理_v28/021.json` — 完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/024.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/027.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/029.json` — 完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/032.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/039.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/040.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `006_bank_06_投诉建议处理_v28/054.json` — 完全相同 target_answer 形成大簇

### `008_chain_restaurant_02_海底捞服务_v28`

场景统计：有效=46，完整Answer唯一率=84.8%，最大完全重复簇=8.7%，可疑样本=8。

- ⚠ `008_chain_restaurant_02_海底捞服务_v28/006.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/016.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/017.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/021.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/023.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/033.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/039.json` — enum anchor 未命中（强可疑）
- ⚠ `008_chain_restaurant_02_海底捞服务_v28/056.json` — enum anchor 未命中（强可疑）

### `009_chain_restaurant_03_星巴克门店运营_v28`

场景统计：有效=48，完整Answer唯一率=97.9%，最大完全重复簇=4.2%，可疑样本=5。

- ⚠ `009_chain_restaurant_03_星巴克门店运营_v28/007.json` — enum anchor 未命中（强可疑）
- ⚠ `009_chain_restaurant_03_星巴克门店运营_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `009_chain_restaurant_03_星巴克门店运营_v28/024.json` — enum anchor 未命中（强可疑）
- ⚠ `009_chain_restaurant_03_星巴克门店运营_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `009_chain_restaurant_03_星巴克门店运营_v28/054.json` — enum anchor 未命中（强可疑）

### `012_eleme_02_饿了么商家端_v28`

场景统计：有效=49，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=1。

- ⚠ `012_eleme_02_饿了么商家端_v28/026.json` — enum anchor 未命中（强可疑）

### `015_eleme_06_饿了么会员_v28`

场景统计：有效=48，完整Answer唯一率=100.0%，最大完全重复簇=2.1%，可疑样本=3。

- ⚠ `015_eleme_06_饿了么会员_v28/010.json` — enum anchor 未命中（强可疑）
- ⚠ `015_eleme_06_饿了么会员_v28/044.json` — enum anchor 未命中（强可疑）
- ⚠ `015_eleme_06_饿了么会员_v28/053.json` — enum anchor 未命中（强可疑）

### `017_eleme_08_饿了么企业版_v28`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=3。

- ⚠ `017_eleme_08_饿了么企业版_v28/005.json` — enum anchor 未命中（强可疑）
- ⚠ `017_eleme_08_饿了么企业版_v28/035.json` — enum anchor 未命中（强可疑）
- ⚠ `017_eleme_08_饿了么企业版_v28/063.json` — enum anchor 未命中（强可疑）

### `019_eleme_10_饿了么物流管理_v28`

场景统计：有效=50，完整Answer唯一率=66.0%，最大完全重复簇=22.0%，可疑样本=24。

- ⚠ `019_eleme_10_饿了么物流管理_v28/002.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/004.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/005.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/007.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/009.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/010.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/013.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/015.json` — enum anchor 未命中（强可疑）
- ⚠ `019_eleme_10_饿了么物流管理_v28/018.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/024.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/025.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/026.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/028.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/031.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/033.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/035.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/037.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/039.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/041.json` — 除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/044.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/048.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/051.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/054.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `019_eleme_10_饿了么物流管理_v28/057.json` — enum anchor 未命中（强可疑）

### `022_eleme_16_饿了么评价管理_v28`

场景统计：有效=52，完整Answer唯一率=100.0%，最大完全重复簇=1.9%，可疑样本=1。

- ⚠ `022_eleme_16_饿了么评价管理_v28/003.json` — enum anchor 未命中（强可疑）

### `026_insurance_03_保单变更流程_v28`

场景统计：有效=48，完整Answer唯一率=81.2%，最大完全重复簇=16.7%，可疑样本=10。

- ⚠ `026_insurance_03_保单变更流程_v28/004.json` — 完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/006.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/008.json` — enum anchor 未命中（强可疑）
- ⚠ `026_insurance_03_保单变更流程_v28/013.json` — enum anchor 未命中（强可疑）
- ⚠ `026_insurance_03_保单变更流程_v28/015.json` — 完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/016.json` — 完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/030.json` — 完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/035.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/038.json` — 完全相同 target_answer 形成大簇
- ⚠ `026_insurance_03_保单变更流程_v28/065.json` — 完全相同 target_answer 形成大簇

### `028_insurance_05_保险客户投诉处理_v28`

场景统计：有效=52，完整Answer唯一率=71.2%，最大完全重复簇=30.8%，可疑样本=16。

- ⚠ `028_insurance_05_保险客户投诉处理_v28/001.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/004.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/008.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/011.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/013.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/018.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/023.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/027.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/030.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/032.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/036.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/039.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/040.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/049.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/056.json` — 完全相同 target_answer 形成大簇
- ⚠ `028_insurance_05_保险客户投诉处理_v28/060.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇

### `030_insurance_07_查勘定损流程_v28`

场景统计：有效=48，完整Answer唯一率=97.9%，最大完全重复簇=4.2%，可疑样本=1。

- ⚠ `030_insurance_07_查勘定损流程_v28/025.json` — enum anchor 未命中（强可疑）

### `032_insurance_12_反欺诈调查流程_v28`

场景统计：有效=50，完整Answer唯一率=92.0%，最大完全重复簇=4.0%，可疑样本=1。

- ⚠ `032_insurance_12_反欺诈调查流程_v28/040.json` — enum anchor 未命中（强可疑）

### `033_jingdong_01_七天无理由退货_v28`

场景统计：有效=51，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=1。

- ⚠ `033_jingdong_01_七天无理由退货_v28/033.json` — enum anchor 未命中（强可疑）

### `034_jingdong_02_商品质量问题退货_v28`

场景统计：有效=50，完整Answer唯一率=76.0%，最大完全重复簇=4.0%，可疑样本=1。

- ⚠ `034_jingdong_02_商品质量问题退货_v28/034.json` — enum anchor 未命中（强可疑）

### `036_jingdong_04_仅退款不退货_v28`

场景统计：有效=48，完整Answer唯一率=77.1%，最大完全重复簇=4.2%，可疑样本=1。

- ⚠ `036_jingdong_04_仅退款不退货_v28/033.json` — enum anchor 未命中（强可疑）

### `037_jingdong_05_30天价保申请_v28`

场景统计：有效=51，完整Answer唯一率=94.1%，最大完全重复簇=5.9%，可疑样本=1。

- ⚠ `037_jingdong_05_30天价保申请_v28/008.json` — enum anchor 未命中（强可疑）

### `038_jingdong_07_订单信息修改_v28`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=12。

- ⚠ `038_jingdong_07_订单信息修改_v28/010.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/015.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/017.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/020.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/021.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/034.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/040.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/041.json` — enum anchor 未命中（强可疑）
- ⚠ `038_jingdong_07_订单信息修改_v28/049.json` — enum anchor 未命中（强可疑）

### `039_jingdong_08_物流异常处理_v28`

场景统计：有效=50，完整Answer唯一率=94.0%，最大完全重复簇=4.0%，可疑样本=1。

- ⚠ `039_jingdong_08_物流异常处理_v28/005.json` — enum anchor 未命中（强可疑）

### `045_jingdong_14_京东服务__v28`

场景统计：有效=49，完整Answer唯一率=93.9%，最大完全重复簇=4.1%，可疑样本=1。

- ⚠ `045_jingdong_14_京东服务__v28/055.json` — enum anchor 未命中（强可疑）

### `046_jingdong_16_企业购_v28`

场景统计：有效=47，完整Answer唯一率=97.9%，最大完全重复簇=4.3%，可疑样本=7。

- ⚠ `046_jingdong_16_企业购_v28/003.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/005.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/015.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/017.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/018.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/023.json` — enum anchor 未命中（强可疑）
- ⚠ `046_jingdong_16_企业购_v28/027.json` — enum anchor 未命中（强可疑）

### `048_jingdong_18_交易纠纷仲裁_v28`

场景统计：有效=51，完整Answer唯一率=92.2%，最大完全重复簇=3.9%，可疑样本=1。

- ⚠ `048_jingdong_18_交易纠纷仲裁_v28/046.json` — enum anchor 未命中（强可疑）

### `049_meituan_01_外卖配送_v28`

场景统计：有效=50，完整Answer唯一率=96.0%，最大完全重复簇=4.0%，可疑样本=1。

- ⚠ `049_meituan_01_外卖配送_v28/054.json` — enum anchor 未命中（强可疑）

### `050_meituan_03_酒店旅游_v28`

场景统计：有效=50，完整Answer唯一率=72.0%，最大完全重复簇=18.0%，可疑样本=11。

- ⚠ `050_meituan_03_酒店旅游_v28/004.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/005.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/011.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/016.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/024.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/027.json` — 除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/032.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/034.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/036.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/039.json` — 完全相同 target_answer 形成大簇；除 enum 外的结构/自由字段相同
- ⚠ `050_meituan_03_酒店旅游_v28/057.json` — 除 enum 外的结构/自由字段相同

### `055_meituan_08_美团外卖运营_v28`

场景统计：有效=53，完整Answer唯一率=92.5%，最大完全重复簇=9.4%，可疑样本=3。

- ⚠ `055_meituan_08_美团外卖运营_v28/016.json` — enum anchor 未命中（强可疑）
- ⚠ `055_meituan_08_美团外卖运营_v28/035.json` — enum anchor 未命中（强可疑）
- ⚠ `055_meituan_08_美团外卖运营_v28/036.json` — enum anchor 未命中（强可疑）

### `056_meituan_08_美团打车_v28`

场景统计：有效=54，完整Answer唯一率=98.1%，最大完全重复簇=3.7%，可疑样本=1。

- ⚠ `056_meituan_08_美团打车_v28/056.json` — enum anchor 未命中（强可疑）

### `058_meituan_10_美团充电宝_v28`

场景统计：有效=53，完整Answer唯一率=71.7%，最大完全重复簇=5.7%，可疑样本=2。

- ⚠ `058_meituan_10_美团充电宝_v28/035.json` — enum anchor 未命中（强可疑）
- ⚠ `058_meituan_10_美团充电宝_v28/036.json` — enum anchor 未命中（强可疑）

### `059_meituan_11_美团会员_v28`

场景统计：有效=50，完整Answer唯一率=98.0%，最大完全重复簇=4.0%，可疑样本=1。

- ⚠ `059_meituan_11_美团会员_v28/025.json` — enum anchor 未命中（强可疑）

### `060_meituan_12_美团客服_v28`

场景统计：有效=50，完整Answer唯一率=62.0%，最大完全重复簇=6.0%，可疑样本=2。

- ⚠ `060_meituan_12_美团客服_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `060_meituan_12_美团客服_v28/034.json` — enum anchor 未命中（强可疑）

### `063_meituan_15_美团闪购商家端_v28`

场景统计：有效=48，完整Answer唯一率=97.9%，最大完全重复簇=4.2%，可疑样本=3。

- ⚠ `063_meituan_15_美团闪购商家端_v28/007.json` — enum anchor 未命中（强可疑）
- ⚠ `063_meituan_15_美团闪购商家端_v28/013.json` — enum anchor 未命中（强可疑）
- ⚠ `063_meituan_15_美团闪购商家端_v28/051.json` — enum anchor 未命中（强可疑）

### `067_meituan_22_美团企业版_v28`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=8。

- ⚠ `067_meituan_22_美团企业版_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/018.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/019.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/024.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/027.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/039.json` — enum anchor 未命中（强可疑）
- ⚠ `067_meituan_22_美团企业版_v28/045.json` — enum anchor 未命中（强可疑）

### `068_meituan_23_美团金融_v28`

场景统计：有效=47，完整Answer唯一率=61.7%，最大完全重复簇=6.4%，可疑样本=3。

- ⚠ `068_meituan_23_美团金融_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `068_meituan_23_美团金融_v28/030.json` — enum anchor 未命中（强可疑）
- ⚠ `068_meituan_23_美团金融_v28/057.json` — enum anchor 未命中（强可疑）

### `069_meituan_24_美团直播_v28`

场景统计：有效=50，完整Answer唯一率=38.0%，最大完全重复簇=16.0%，可疑样本=30。

- ⚠ `069_meituan_24_美团直播_v28/002.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/004.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/005.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/007.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/008.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/009.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/010.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/013.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/015.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/016.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/017.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/022.json` — 完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/023.json` — 完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/025.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/027.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/031.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/032.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/033.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/034.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/036.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/040.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/041.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/042.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/052.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/056.json` — enum anchor 未命中（强可疑）
- ⚠ `069_meituan_24_美团直播_v28/063.json` — enum anchor 未命中（强可疑）；完全相同 target_answer 形成大簇
- ⚠ `069_meituan_24_美团直播_v28/065.json` — enum anchor 未命中（强可疑）

### `075_payment_06_支付风控解冻_v28`

场景统计：有效=54，完整Answer唯一率=55.6%，最大完全重复簇=7.4%，可疑样本=44。

- ⚠ `075_payment_06_支付风控解冻_v28/002.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/003.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/004.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/005.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/008.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/009.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/010.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/011.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/012.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/013.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/014.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/015.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/019.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/020.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/021.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/022.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/023.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/024.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/025.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/026.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/027.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/028.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `075_payment_06_支付风控解冻_v28/030.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/031.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/034.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/036.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/037.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/038.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/039.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/040.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/041.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/042.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/043.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/045.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/046.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/048.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/049.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/051.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/052.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/053.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/055.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/056.json` — 除 enum 外的结构/自由字段相同
- ⚠ `075_payment_06_支付风控解冻_v28/057.json` — 除 enum 外的结构/自由字段相同

### `076_pdd_01_百亿补贴_v28`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=1。

- ⚠ `076_pdd_01_百亿补贴_v28/019.json` — enum anchor 未命中（强可疑）

### `079_pdd_04_多多买菜_v28`

场景统计：有效=52，完整Answer唯一率=100.0%，最大完全重复簇=1.9%，可疑样本=1。

- ⚠ `079_pdd_04_多多买菜_v28/010.json` — enum anchor 未命中（强可疑）

### `080_pdd_06_多多进宝_v28`

场景统计：有效=54，完整Answer唯一率=53.7%，最大完全重复簇=7.4%，可疑样本=2。

- ⚠ `080_pdd_06_多多进宝_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `080_pdd_06_多多进宝_v28/035.json` — enum anchor 未命中（强可疑）

### `081_pdd_07_多多直播_v28`

场景统计：有效=50，完整Answer唯一率=72.0%，最大完全重复簇=6.0%，可疑样本=25。

- ⚠ `081_pdd_07_多多直播_v28/003.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/005.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/008.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/010.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/011.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/015.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/016.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/017.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/019.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/020.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/022.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/023.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/024.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/027.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/030.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/032.json` — enum anchor 未命中（强可疑）；除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/035.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/037.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/038.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/039.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/041.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/044.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/045.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/056.json` — 除 enum 外的结构/自由字段相同
- ⚠ `081_pdd_07_多多直播_v28/059.json` — 除 enum 外的结构/自由字段相同

### `082_pdd_09_多多国际_v28`

场景统计：有效=46，完整Answer唯一率=91.3%，最大完全重复簇=8.7%，可疑样本=13。

- ⚠ `082_pdd_09_多多国际_v28/003.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/004.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/005.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/008.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/023.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/027.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/030.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/036.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/040.json` — enum anchor 未命中（强可疑）
- ⚠ `082_pdd_09_多多国际_v28/041.json` — enum anchor 未命中（强可疑）

### `083_pdd_10_假一赔十_v28`

场景统计：有效=51，完整Answer唯一率=94.1%，最大完全重复簇=3.9%，可疑样本=1。

- ⚠ `083_pdd_10_假一赔十_v28/034.json` — enum anchor 未命中（强可疑）

### `084_pdd_13_砍价免费拿_v28`

场景统计：有效=50，完整Answer唯一率=98.0%，最大完全重复簇=4.0%，可疑样本=2。

- ⚠ `084_pdd_13_砍价免费拿_v28/004.json` — enum anchor 未命中（强可疑）
- ⚠ `084_pdd_13_砍价免费拿_v28/041.json` — enum anchor 未命中（强可疑）

### `086_pdd_17_多多批发_v28`

场景统计：有效=51，完整Answer唯一率=76.5%，最大完全重复簇=3.9%，可疑样本=3。

- ⚠ `086_pdd_17_多多批发_v28/018.json` — enum anchor 未命中（强可疑）
- ⚠ `086_pdd_17_多多批发_v28/053.json` — enum anchor 未命中（强可疑）
- ⚠ `086_pdd_17_多多批发_v28/054.json` — enum anchor 未命中（强可疑）

### `088_pdd_20_多多爱消除_v28`

场景统计：有效=51，完整Answer唯一率=90.2%，最大完全重复簇=5.9%，可疑样本=5。

- ⚠ `088_pdd_20_多多爱消除_v28/002.json` — enum anchor 未命中（强可疑）
- ⚠ `088_pdd_20_多多爱消除_v28/014.json` — enum anchor 未命中（强可疑）
- ⚠ `088_pdd_20_多多爱消除_v28/039.json` — enum anchor 未命中（强可疑）
- ⚠ `088_pdd_20_多多爱消除_v28/042.json` — enum anchor 未命中（强可疑）
- ⚠ `088_pdd_20_多多爱消除_v28/044.json` — enum anchor 未命中（强可疑）

### `090_taobao_02_闲鱼二手交易_v28`

场景统计：有效=53，完整Answer唯一率=96.2%，最大完全重复簇=5.7%，可疑样本=2。

- ⚠ `090_taobao_02_闲鱼二手交易_v28/018.json` — enum anchor 未命中（强可疑）
- ⚠ `090_taobao_02_闲鱼二手交易_v28/044.json` — enum anchor 未命中（强可疑）

### `091_taobao_07_淘宝联盟推广_v28`

场景统计：有效=50，完整Answer唯一率=68.0%，最大完全重复簇=6.0%，可疑样本=1。

- ⚠ `091_taobao_07_淘宝联盟推广_v28/024.json` — enum anchor 未命中（强可疑）

### `092_taobao_08_discount_v28`

场景统计：有效=47，完整Answer唯一率=95.7%，最大完全重复簇=6.4%，可疑样本=5。

- ⚠ `092_taobao_08_discount_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `092_taobao_08_discount_v28/024.json` — enum anchor 未命中（强可疑）
- ⚠ `092_taobao_08_discount_v28/025.json` — enum anchor 未命中（强可疑）
- ⚠ `092_taobao_08_discount_v28/027.json` — enum anchor 未命中（强可疑）
- ⚠ `092_taobao_08_discount_v28/028.json` — enum anchor 未命中（强可疑）

### `093_taobao_10_千牛商家服务_v28`

场景统计：有效=50，完整Answer唯一率=96.0%，最大完全重复簇=4.0%，可疑样本=4。

- ⚠ `093_taobao_10_千牛商家服务_v28/002.json` — enum anchor 未命中（强可疑）
- ⚠ `093_taobao_10_千牛商家服务_v28/006.json` — enum anchor 未命中（强可疑）
- ⚠ `093_taobao_10_千牛商家服务_v28/011.json` — enum anchor 未命中（强可疑）
- ⚠ `093_taobao_10_千牛商家服务_v28/054.json` — enum anchor 未命中（强可疑）

### `094_taobao_12_campaign_v28`

场景统计：有效=48，完整Answer唯一率=97.9%，最大完全重复簇=4.2%，可疑样本=1。

- ⚠ `094_taobao_12_campaign_v28/022.json` — enum anchor 未命中（强可疑）

### `095_taobao_14_淘宝租赁_v28`

场景统计：有效=47，完整Answer唯一率=95.7%，最大完全重复簇=4.3%，可疑样本=1。

- ⚠ `095_taobao_14_淘宝租赁_v28/008.json` — enum anchor 未命中（强可疑）

### `098_telecom_02_中国联通客服_v28`

场景统计：有效=50，完整Answer唯一率=98.0%，最大完全重复簇=4.0%，可疑样本=4。

- ⚠ `098_telecom_02_中国联通客服_v28/037.json` — enum anchor 未命中（强可疑）
- ⚠ `098_telecom_02_中国联通客服_v28/039.json` — enum anchor 未命中（强可疑）
- ⚠ `098_telecom_02_中国联通客服_v28/041.json` — enum anchor 未命中（强可疑）
- ⚠ `098_telecom_02_中国联通客服_v28/068.json` — enum anchor 未命中（强可疑）

### `099_telecom_03_中国电信客服_v28`

场景统计：有效=53，完整Answer唯一率=96.2%，最大完全重复簇=5.7%，可疑样本=3。

- ⚠ `099_telecom_03_中国电信客服_v28/013.json` — enum anchor 未命中（强可疑）
- ⚠ `099_telecom_03_中国电信客服_v28/028.json` — enum anchor 未命中（强可疑）
- ⚠ `099_telecom_03_中国电信客服_v28/059.json` — enum anchor 未命中（强可疑）

### `100_01_reusable_container`

场景统计：有效=47，完整Answer唯一率=61.7%，最大完全重复簇=6.4%，可疑样本=1。

- ⚠ `100_01_reusable_container/018.json` — enum anchor 未命中（强可疑）

### `102_03_city_museum_pass`

场景统计：有效=51，完整Answer唯一率=58.8%，最大完全重复簇=5.9%，可疑样本=3。

- ⚠ `102_03_city_museum_pass/006.json` — enum anchor 未命中（强可疑）
- ⚠ `102_03_city_museum_pass/011.json` — enum anchor 未命中（强可疑）
- ⚠ `102_03_city_museum_pass/028.json` — enum anchor 未命中（强可疑）

### `103_04_fleet_maintenance`

场景统计：有效=48，完整Answer唯一率=60.4%，最大完全重复簇=6.2%，可疑样本=2。

- ⚠ `103_04_fleet_maintenance/018.json` — enum anchor 未命中（强可疑）
- ⚠ `103_04_fleet_maintenance/026.json` — enum anchor 未命中（强可疑）

### `104_05_corporate_fitness_pass`

场景统计：有效=47，完整Answer唯一率=66.0%，最大完全重复簇=6.4%，可疑样本=2。

- ⚠ `104_05_corporate_fitness_pass/014.json` — enum anchor 未命中（强可疑）
- ⚠ `104_05_corporate_fitness_pass/026.json` — enum anchor 未命中（强可疑）

### `105_06_corporate_dental_screening`

场景统计：有效=51，完整Answer唯一率=60.8%，最大完全重复簇=5.9%，可疑样本=1。

- ⚠ `105_06_corporate_dental_screening/026.json` — enum anchor 未命中（强可疑）

### `108_09_it_asset_recovery`

场景统计：有效=50，完整Answer唯一率=56.0%，最大完全重复簇=6.0%，可疑样本=2。

- ⚠ `108_09_it_asset_recovery/018.json` — enum anchor 未命中（强可疑）
- ⚠ `108_09_it_asset_recovery/043.json` — enum anchor 未命中（强可疑）

### `110_01_piano_tuning`

场景统计：有效=52，完整Answer唯一率=73.1%，最大完全重复簇=5.8%，可疑样本=3。

- ⚠ `110_01_piano_tuning/015.json` — enum anchor 未命中（强可疑）
- ⚠ `110_01_piano_tuning/025.json` — enum anchor 未命中（强可疑）
- ⚠ `110_01_piano_tuning/030.json` — enum anchor 未命中（强可疑）

### `111_02_moving_estimate`

场景统计：有效=51，完整Answer唯一率=70.6%，最大完全重复簇=7.8%，可疑样本=2。

- ⚠ `111_02_moving_estimate/025.json` — enum anchor 未命中（强可疑）
- ⚠ `111_02_moving_estimate/033.json` — enum anchor 未命中（强可疑）

### `112_03_air_sampling`

场景统计：有效=52，完整Answer唯一率=65.4%，最大完全重复簇=5.8%，可疑样本=1。

- ⚠ `112_03_air_sampling/025.json` — enum anchor 未命中（强可疑）

### `113_04_office_plant_care`

场景统计：有效=46，完整Answer唯一率=67.4%，最大完全重复簇=6.5%，可疑样本=1。

- ⚠ `113_04_office_plant_care/025.json` — enum anchor 未命中（强可疑）

### `114_05_pet_grooming`

场景统计：有效=50，完整Answer唯一率=70.0%，最大完全重复簇=8.0%，可疑样本=2。

- ⚠ `114_05_pet_grooming/015.json` — enum anchor 未命中（强可疑）
- ⚠ `114_05_pet_grooming/025.json` — enum anchor 未命中（强可疑）

### `115_06_moveout_inspection`

场景统计：有效=47，完整Answer唯一率=68.1%，最大完全重复簇=6.4%，可疑样本=3。

- ⚠ `115_06_moveout_inspection/011.json` — enum anchor 未命中（强可疑）
- ⚠ `115_06_moveout_inspection/025.json` — enum anchor 未命中（强可疑）
- ⚠ `115_06_moveout_inspection/033.json` — enum anchor 未命中（强可疑）

### `116_07_aging_in_place`

场景统计：有效=48，完整Answer唯一率=64.6%，最大完全重复簇=8.3%，可疑样本=3。

- ⚠ `116_07_aging_in_place/011.json` — enum anchor 未命中（强可疑）
- ⚠ `116_07_aging_in_place/025.json` — enum anchor 未命中（强可疑）
- ⚠ `116_07_aging_in_place/033.json` — enum anchor 未命中（强可疑）

### `117_08_document_destruction`

场景统计：有效=53，完整Answer唯一率=64.2%，最大完全重复簇=7.5%，可疑样本=5。

- ⚠ `117_08_document_destruction/005.json` — enum anchor 未命中（强可疑）
- ⚠ `117_08_document_destruction/011.json` — enum anchor 未命中（强可疑）
- ⚠ `117_08_document_destruction/025.json` — enum anchor 未命中（强可疑）
- ⚠ `117_08_document_destruction/027.json` — enum anchor 未命中（强可疑）
- ⚠ `117_08_document_destruction/033.json` — enum anchor 未命中（强可疑）

### `118_09_corporate_headshot`

场景统计：有效=46，完整Answer唯一率=69.6%，最大完全重复簇=8.7%，可疑样本=5。

- ⚠ `118_09_corporate_headshot/010.json` — enum anchor 未命中（强可疑）
- ⚠ `118_09_corporate_headshot/011.json` — enum anchor 未命中（强可疑）
- ⚠ `118_09_corporate_headshot/025.json` — enum anchor 未命中（强可疑）
- ⚠ `118_09_corporate_headshot/033.json` — enum anchor 未命中（强可疑）
- ⚠ `118_09_corporate_headshot/059.json` — enum anchor 未命中（强可疑）

### `119_10_suit_measurement`

场景统计：有效=49，完整Answer唯一率=71.4%，最大完全重复簇=6.1%，可疑样本=4。

- ⚠ `119_10_suit_measurement/007.json` — enum anchor 未命中（强可疑）
- ⚠ `119_10_suit_measurement/011.json` — enum anchor 未命中（强可疑）
- ⚠ `119_10_suit_measurement/025.json` — enum anchor 未命中（强可疑）
- ⚠ `119_10_suit_measurement/028.json` — enum anchor 未命中（强可疑）

### `121_01_smart_locker`

场景统计：有效=45，完整Answer唯一率=100.0%，最大完全重复簇=2.2%，可疑样本=18。

- ⚠ `121_01_smart_locker/004.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/007.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/009.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/010.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/013.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/015.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/016.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/021.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/024.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/026.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/028.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/029.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/035.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/038.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/041.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/042.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/043.json` — enum anchor 未命中（强可疑）
- ⚠ `121_01_smart_locker/053.json` — enum anchor 未命中（强可疑）

### `122_02_pet_clinic`

场景统计：有效=49，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=7。

- ⚠ `122_02_pet_clinic/010.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/024.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/034.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/036.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/038.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/041.json` — enum anchor 未命中（强可疑）
- ⚠ `122_02_pet_clinic/055.json` — enum anchor 未命中（强可疑）

### `123_03_public_library`

场景统计：有效=43，完整Answer唯一率=100.0%，最大完全重复簇=2.3%，可疑样本=8。

- ⚠ `123_03_public_library/007.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/013.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/016.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/026.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/029.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/033.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/039.json` — enum anchor 未命中（强可疑）
- ⚠ `123_03_public_library/043.json` — enum anchor 未命中（强可疑）

### `124_04_parking_pass`

场景统计：有效=46，完整Answer唯一率=100.0%，最大完全重复簇=2.2%，可疑样本=16。

- ⚠ `124_04_parking_pass/005.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/008.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/011.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/012.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/014.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/016.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/021.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/027.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/030.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/031.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/032.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/037.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/039.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/040.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/042.json` — enum anchor 未命中（强可疑）
- ⚠ `124_04_parking_pass/063.json` — enum anchor 未命中（强可疑）

### `125_05_ev_charging`

场景统计：有效=47，完整Answer唯一率=100.0%，最大完全重复簇=2.1%，可疑样本=12。

- ⚠ `125_05_ev_charging/002.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/003.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/012.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/014.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/020.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/027.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/030.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/036.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/037.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/038.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/039.json` — enum anchor 未命中（强可疑）
- ⚠ `125_05_ev_charging/042.json` — enum anchor 未命中（强可疑）

### `126_06_fitness_class`

场景统计：有效=52，完整Answer唯一率=100.0%，最大完全重复簇=1.9%，可疑样本=15。

- ⚠ `126_06_fitness_class/007.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/009.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/012.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/016.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/020.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/027.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/034.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/036.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/038.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/039.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/041.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/042.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/055.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/060.json` — enum anchor 未命中（强可疑）
- ⚠ `126_06_fitness_class/065.json` — enum anchor 未命中（强可疑）

### `127_07_laundry_care`

场景统计：有效=48，完整Answer唯一率=100.0%，最大完全重复簇=2.1%，可疑样本=9。

- ⚠ `127_07_laundry_care/005.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/009.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/019.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/020.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/021.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/024.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/025.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/039.json` — enum anchor 未命中（强可疑）
- ⚠ `127_07_laundry_care/042.json` — enum anchor 未命中（强可疑）

### `128_08_coworking_room`

场景统计：有效=49，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=20。

- ⚠ `128_08_coworking_room/005.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/007.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/010.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/013.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/014.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/015.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/020.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/021.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/025.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/027.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/029.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/037.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/038.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/039.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/042.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/043.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/045.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/051.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/057.json` — enum anchor 未命中（强可疑）
- ⚠ `128_08_coworking_room/065.json` — enum anchor 未命中（强可疑）

### `129_09_lab_instrument`

场景统计：有效=44，完整Answer唯一率=100.0%，最大完全重复簇=2.3%，可疑样本=14。

- ⚠ `129_09_lab_instrument/007.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/009.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/019.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/021.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/025.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/029.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/031.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/036.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/038.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/040.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/041.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/042.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/043.json` — enum anchor 未命中（强可疑）
- ⚠ `129_09_lab_instrument/051.json` — enum anchor 未命中（强可疑）

### `130_10_cloud_printing`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=12。

- ⚠ `130_10_cloud_printing/005.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/013.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/016.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/021.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/025.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/029.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/034.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/040.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/041.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/042.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/053.json` — enum anchor 未命中（强可疑）
- ⚠ `130_10_cloud_printing/057.json` — enum anchor 未命中（强可疑）

### `131_01_delivery_progress`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=8。

- ⚠ `131_01_delivery_progress/011.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/027.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/028.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/029.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/030.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/031.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/032.json` — enum anchor 未命中（强可疑）
- ⚠ `131_01_delivery_progress/033.json` — enum anchor 未命中（强可疑）

### `132_06_jingdong_invoice_reissue_v28`

场景统计：有效=50，完整Answer唯一率=100.0%，最大完全重复簇=2.0%，可疑样本=8。

- ⚠ `132_06_jingdong_invoice_reissue_v28/017.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/025.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/029.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/030.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/034.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/036.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/038.json` — enum anchor 未命中（强可疑）
- ⚠ `132_06_jingdong_invoice_reissue_v28/043.json` — enum anchor 未命中（强可疑）

## 使用建议

1. `ANCHOR_MISMATCH` 先排除或重新生成，除非 Requirements 能证明该 anchor 本身不可达。
2. 对抽取型、要素型场景优先检查 `ENUM_ONLY_VARIATION`；为自由文本、数值、数组长度和业务对象增加 coverage 轴，而不是继续只增加 enum 样本。
3. 对固定话术分类场景，重复 Answer 可以保留，但必须检查 Input 是否覆盖不同表达、历史状态和边界证据。
4. 最终入库仍需独立盲回推验证；Schema-valid 和本报告未标记都不能单独等价为 gold。
5. 后续新 Input 使用可判别模糊模式时，建议保留 `input_ambiguity_requested` 字段，并单独统计其盲回推通过率。
