# Target Answer 完全重复度坍缩审计

> 本报告只比较同一场景内完整 `target_answer` 的 JSON 结构和值。对象键顺序被规范化，数组顺序和值保持不变。它不使用 Input、enum 屏蔽、默认值比例、CoT 或最终 Answer。

## 口径

设一个场景有 `N` 条身份正确、且通过当前 Output JSON Schema 的 Target Answer，规范化后有 `U` 个不同 Answer。

- **唯一率**：`U / N`。
- **重复冗余率**：`(N-U) / N`；表示去除每种 Answer 的第一条后，剩余重复出现占比。
- **重复样本覆盖率**：所有属于重复组（组大小≥2）的样本数除以 `N`。
- **最大重复簇占比**：出现次数最多的一个完整 Answer 占 `N` 的比例。这是判断单一模式坍缩最直接的指标。
- **随机碰撞率**：从该场景随机抽两条，它们的完整 Answer 完全相同的概率。

只在 `N≥20` 时给出坍缩等级；更少的样本统一标记 `INSUFFICIENT`，不做分布结论。

| 等级 | 客观阈值 |
|---|---|
| `SEVERE` | 最大重复簇占比 ≥ 50% |
| `HIGH` | 最大重复簇占比 ≥ 30%，或随机碰撞率 ≥ 15% |
| `REVIEW` | 最大重复簇占比 ≥ 15%，或重复冗余率 ≥ 50% |
| `LOW` | 未命中以上阈值 |
| `INSUFFICIENT` | 可分析 Target Answer 少于20条 |

这些等级表示**完整 Answer 的经验集中度**，不直接断言业务错误。固定分类、固定话术或可达答案空间很小的场景，本来就可能重复；但检测指标本身不会受此解释影响。

生成时间：`2026-08-15T02:14:05+08:00`

## 运行目录 `gemini_all_1`

- 路径：`/Users/liyong90/Desktop/sop-maze/answer_first_input_synthesis_20260813/runs/gemini_all_1`
- 快照编号文件：8877
- 场景数：131
- 等级分布：`{"HIGH": 1, "LOW": 124, "REVIEW": 6}`
- 文件状态分布：`{"candidate": 7101, "input_error": 51, "target_error": 1691, "target_ready": 34}`
- 排除原因：`{"missing_target_answer": 1691}`

### 场景汇总

| 等级 | 场景 | N | U/唯一率 | 重复冗余率 | 重复样本覆盖率 | 最大簇 | Top3占比 | 随机碰撞率 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `HIGH` | `028_insurance_05_保险客户投诉处理_v28` | 55 | 39 / 70.9% | 29.1% | 30.9% | 17 / 30.9% | 34.5% | 9.2% |
| `REVIEW` | `006_bank_06_投诉建议处理_v28` | 54 | 40 / 74.1% | 25.9% | 27.8% | 15 / 27.8% | 31.5% | 7.3% |
| `REVIEW` | `019_eleme_10_饿了么物流管理_v28` | 55 | 38 / 69.1% | 30.9% | 38.2% | 11 / 20.0% | 34.5% | 4.6% |
| `REVIEW` | `026_insurance_03_保单变更流程_v28` | 55 | 45 / 81.8% | 18.2% | 23.6% | 9 / 16.4% | 23.6% | 2.6% |
| `REVIEW` | `050_meituan_03_酒店旅游_v28` | 56 | 41 / 73.2% | 26.8% | 35.7% | 9 / 16.1% | 28.6% | 3.1% |
| `REVIEW` | `069_meituan_24_美团直播_v28` | 57 | 20 / 35.1% | 64.9% | 82.5% | 9 / 15.8% | 42.1% | 7.5% |
| `REVIEW` | `080_pdd_06_多多进宝_v28` | 59 | 29 / 49.2% | 50.8% | 91.5% | 4 / 6.8% | 16.9% | 2.2% |
| `LOW` | `097_telecom_01_中国移动客服_v28` | 57 | 48 / 84.2% | 15.8% | 21.1% | 7 / 12.3% | 21.1% | 1.6% |
| `LOW` | `008_chain_restaurant_02_海底捞服务_v28` | 53 | 41 / 77.4% | 22.6% | 34.0% | 5 / 9.4% | 22.6% | 1.6% |
| `LOW` | `037_jingdong_05_30天价保申请_v28` | 58 | 53 / 91.4% | 8.6% | 12.1% | 5 / 8.6% | 13.8% | 0.7% |
| `LOW` | `055_meituan_08_美团外卖运营_v28` | 59 | 55 / 93.2% | 6.8% | 8.5% | 5 / 8.5% | 11.9% | 0.6% |
| `LOW` | `113_04_office_plant_care` | 51 | 33 / 64.7% | 35.3% | 60.8% | 4 / 7.8% | 19.6% | 1.9% |
| `LOW` | `115_06_moveout_inspection` | 53 | 34 / 64.2% | 35.8% | 60.4% | 4 / 7.5% | 18.9% | 1.9% |
| `LOW` | `118_09_corporate_headshot` | 53 | 35 / 66.0% | 34.0% | 56.6% | 4 / 7.5% | 20.8% | 1.9% |
| `LOW` | `116_07_aging_in_place` | 54 | 34 / 63.0% | 37.0% | 61.1% | 4 / 7.4% | 20.4% | 2.0% |
| `LOW` | `114_05_pet_grooming` | 54 | 36 / 66.7% | 33.3% | 53.7% | 4 / 7.4% | 20.4% | 1.9% |
| `LOW` | `119_10_suit_measurement` | 54 | 36 / 66.7% | 33.3% | 55.6% | 4 / 7.4% | 18.5% | 1.7% |
| `LOW` | `082_pdd_09_多多国际_v28` | 54 | 49 / 90.7% | 9.3% | 14.8% | 4 / 7.4% | 14.8% | 0.6% |
| `LOW` | `111_02_moving_estimate` | 55 | 37 / 67.3% | 32.7% | 54.5% | 4 / 7.3% | 18.2% | 1.7% |
| `LOW` | `086_pdd_17_多多批发_v28` | 56 | 42 / 75.0% | 25.0% | 46.4% | 4 / 7.1% | 14.3% | 1.1% |
| `LOW` | `108_09_it_asset_recovery` | 57 | 30 / 52.6% | 47.4% | 87.7% | 4 / 7.0% | 17.5% | 2.0% |
| `LOW` | `117_08_document_destruction` | 57 | 36 / 63.2% | 36.8% | 56.1% | 4 / 7.0% | 21.1% | 2.2% |
| `LOW` | `003_bank_03_转账异常处理_v28` | 57 | 44 / 77.2% | 22.8% | 42.1% | 4 / 7.0% | 14.0% | 1.0% |
| `LOW` | `075_payment_06_支付风控解冻_v28` | 58 | 32 / 55.2% | 44.8% | 70.7% | 4 / 6.9% | 17.2% | 2.3% |
| `LOW` | `100_01_reusable_container` | 53 | 30 / 56.6% | 43.4% | 84.9% | 3 / 5.7% | 13.2% | 1.7% |
| `LOW` | `103_04_fleet_maintenance` | 53 | 31 / 58.5% | 41.5% | 79.2% | 3 / 5.7% | 15.1% | 1.7% |
| `LOW` | `004_bank_04_贷款咨询与申请_v28` | 53 | 43 / 81.1% | 18.9% | 35.8% | 3 / 5.7% | 13.2% | 0.8% |
| `LOW` | `092_taobao_08_discount_v28` | 53 | 51 / 96.2% | 3.8% | 5.7% | 3 / 5.7% | 9.4% | 0.2% |
| `LOW` | `104_05_corporate_fitness_pass` | 54 | 32 / 59.3% | 40.7% | 79.6% | 3 / 5.6% | 13.0% | 1.6% |
| `LOW` | `105_06_corporate_dental_screening` | 54 | 32 / 59.3% | 40.7% | 79.6% | 3 / 5.6% | 13.0% | 1.6% |
| `LOW` | `001_bank_01_信用卡申请审批流程_v28` | 54 | 34 / 63.0% | 37.0% | 64.8% | 3 / 5.6% | 16.7% | 1.7% |
| `LOW` | `021_eleme_13_饿了么跑腿_v28` | 54 | 44 / 81.5% | 18.5% | 35.2% | 3 / 5.6% | 13.0% | 0.8% |
| `LOW` | `027_insurance_04_退保处理流程_v28` | 54 | 47 / 87.0% | 13.0% | 24.1% | 3 / 5.6% | 13.0% | 0.6% |
| `LOW` | `101_02_cold_storage_flex_load` | 55 | 29 / 52.7% | 47.3% | 89.1% | 3 / 5.5% | 16.4% | 2.0% |
| `LOW` | `068_meituan_23_美团金融_v28` | 55 | 31 / 56.4% | 43.6% | 76.4% | 3 / 5.5% | 16.4% | 2.0% |
| `LOW` | `102_03_city_museum_pass` | 55 | 32 / 58.2% | 41.8% | 78.2% | 3 / 5.5% | 16.4% | 1.8% |
| `LOW` | `081_pdd_07_多多直播_v28` | 55 | 40 / 72.7% | 27.3% | 45.5% | 3 / 5.5% | 16.4% | 1.3% |
| `LOW` | `002_bank_02_挂失解挂流程_v28` | 55 | 52 / 94.5% | 5.5% | 9.1% | 3 / 5.5% | 10.9% | 0.3% |
| `LOW` | `109_10_overflow_fulfillment` | 56 | 30 / 53.6% | 46.4% | 89.3% | 3 / 5.4% | 14.3% | 1.8% |
| `LOW` | `060_meituan_12_美团客服_v28` | 56 | 33 / 58.9% | 41.1% | 71.4% | 3 / 5.4% | 16.1% | 1.9% |
| `LOW` | `091_taobao_07_淘宝联盟推广_v28` | 56 | 38 / 67.9% | 32.1% | 57.1% | 3 / 5.4% | 16.1% | 1.4% |
| `LOW` | `110_01_piano_tuning` | 56 | 39 / 69.6% | 30.4% | 53.6% | 3 / 5.4% | 16.1% | 1.4% |
| `LOW` | `088_pdd_20_多多爱消除_v28` | 56 | 50 / 89.3% | 10.7% | 19.6% | 3 / 5.4% | 12.5% | 0.5% |
| `LOW` | `090_taobao_02_闲鱼二手交易_v28` | 56 | 54 / 96.4% | 3.6% | 5.4% | 3 / 5.4% | 8.9% | 0.2% |
| `LOW` | `099_telecom_03_中国电信客服_v28` | 56 | 54 / 96.4% | 3.6% | 5.4% | 3 / 5.4% | 8.9% | 0.2% |
| `LOW` | `106_07_night_reading_bookstore` | 57 | 31 / 54.4% | 45.6% | 86.0% | 3 / 5.3% | 15.8% | 1.8% |
| `LOW` | `112_03_air_sampling` | 57 | 37 / 64.9% | 35.1% | 59.6% | 3 / 5.3% | 15.8% | 1.6% |
| `LOW` | `058_meituan_10_美团充电宝_v28` | 57 | 38 / 66.7% | 33.3% | 64.9% | 3 / 5.3% | 12.3% | 1.3% |
| `LOW` | `078_pdd_03_农产品生鲜_v28` | 51 | 50 / 98.0% | 2.0% | 3.9% | 2 / 3.9% | 7.8% | 0.1% |
| `LOW` | `015_eleme_06_饿了么会员_v28` | 52 | 51 / 98.1% | 1.9% | 3.8% | 2 / 3.8% | 7.7% | 0.1% |
| `LOW` | `107_08_dorm_linen_care` | 53 | 31 / 58.5% | 41.5% | 83.0% | 2 / 3.8% | 11.3% | 1.6% |
| `LOW` | `005_bank_05_理财产品购买流程_v28` | 53 | 47 / 88.7% | 11.3% | 22.6% | 2 / 3.8% | 11.3% | 0.4% |
| `LOW` | `044_jingdong_13_以旧换新_v28` | 53 | 47 / 88.7% | 11.3% | 22.6% | 2 / 3.8% | 11.3% | 0.4% |
| `LOW` | `064_meituan_16_美团闪购用户端_v28` | 53 | 49 / 92.5% | 7.5% | 15.1% | 2 / 3.8% | 11.3% | 0.3% |
| `LOW` | `095_taobao_14_淘宝租赁_v28` | 53 | 50 / 94.3% | 5.7% | 11.3% | 2 / 3.8% | 11.3% | 0.2% |
| `LOW` | `047_jingdong_17_账户被盗申诉处理_v28` | 53 | 51 / 96.2% | 3.8% | 7.5% | 2 / 3.8% | 9.4% | 0.1% |
| `LOW` | `030_insurance_07_查勘定损流程_v28` | 53 | 52 / 98.1% | 1.9% | 3.8% | 2 / 3.8% | 7.5% | 0.1% |
| `LOW` | `046_jingdong_16_企业购_v28` | 53 | 52 / 98.1% | 1.9% | 3.8% | 2 / 3.8% | 7.5% | 0.1% |
| `LOW` | `057_meituan_09_美团买药_v28` | 53 | 52 / 98.1% | 1.9% | 3.8% | 2 / 3.8% | 7.5% | 0.1% |
| `LOW` | `036_jingdong_04_仅退款不退货_v28` | 54 | 39 / 72.2% | 27.8% | 55.6% | 2 / 3.7% | 11.1% | 1.0% |
| `LOW` | `043_jingdong_12_白条分期问题_v28` | 54 | 49 / 90.7% | 9.3% | 18.5% | 2 / 3.7% | 11.1% | 0.3% |
| `LOW` | `061_meituan_13_美团外卖商家端_v28` | 54 | 50 / 92.6% | 7.4% | 14.8% | 2 / 3.7% | 11.1% | 0.3% |
| `LOW` | `074_payment_05_商家退款流程_v28` | 54 | 51 / 94.4% | 5.6% | 11.1% | 2 / 3.7% | 11.1% | 0.2% |
| `LOW` | `016_eleme_07_饿了么客服_v28` | 54 | 52 / 96.3% | 3.7% | 7.4% | 2 / 3.7% | 9.3% | 0.1% |
| `LOW` | `070_payment_01_账户被盗申诉流程_v28` | 54 | 53 / 98.1% | 1.9% | 3.7% | 2 / 3.7% | 7.4% | 0.1% |
| `LOW` | `094_taobao_12_campaign_v28` | 54 | 53 / 98.1% | 1.9% | 3.7% | 2 / 3.7% | 7.4% | 0.1% |
| `LOW` | `039_jingdong_08_物流异常处理_v28` | 55 | 49 / 89.1% | 10.9% | 21.8% | 2 / 3.6% | 10.9% | 0.4% |
| `LOW` | `042_jingdong_11_用户投诉处理_v28` | 55 | 49 / 89.1% | 10.9% | 21.8% | 2 / 3.6% | 10.9% | 0.4% |
| `LOW` | `048_jingdong_18_交易纠纷仲裁_v28` | 55 | 51 / 92.7% | 7.3% | 14.5% | 2 / 3.6% | 10.9% | 0.3% |
| `LOW` | `045_jingdong_14_京东服务__v28` | 55 | 52 / 94.5% | 5.5% | 10.9% | 2 / 3.6% | 10.9% | 0.2% |
| `LOW` | `035_jingdong_03_换货补发处理_v28` | 55 | 53 / 96.4% | 3.6% | 7.3% | 2 / 3.6% | 9.1% | 0.1% |
| `LOW` | `063_meituan_15_美团闪购商家端_v28` | 55 | 53 / 96.4% | 3.6% | 7.3% | 2 / 3.6% | 9.1% | 0.1% |
| `LOW` | `096_taobao_15_天猫奢品_v28` | 55 | 53 / 96.4% | 3.6% | 7.3% | 2 / 3.6% | 9.1% | 0.1% |
| `LOW` | `009_chain_restaurant_03_星巴克门店运营_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `025_insurance_02_理赔资料审核流程_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `059_meituan_11_美团会员_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `066_meituan_21_美团无人配送_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `077_pdd_02_拼团模式_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `084_pdd_13_砍价免费拿_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `087_pdd_18_偏远地区包邮_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `098_telecom_02_中国联通客服_v28` | 55 | 54 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.3% | 0.1% |
| `LOW` | `034_jingdong_02_商品质量问题退货_v28` | 56 | 39 / 69.6% | 30.4% | 60.7% | 2 / 3.6% | 10.7% | 1.1% |
| `LOW` | `065_meituan_17_美团民宿_v28` | 56 | 42 / 75.0% | 25.0% | 50.0% | 2 / 3.6% | 10.7% | 0.9% |
| `LOW` | `032_insurance_12_反欺诈调查流程_v28` | 56 | 50 / 89.3% | 10.7% | 21.4% | 2 / 3.6% | 10.7% | 0.4% |
| `LOW` | `083_pdd_10_假一赔十_v28` | 56 | 50 / 89.3% | 10.7% | 21.4% | 2 / 3.6% | 10.7% | 0.4% |
| `LOW` | `093_taobao_10_千牛商家服务_v28` | 56 | 52 / 92.9% | 7.1% | 14.3% | 2 / 3.6% | 10.7% | 0.3% |
| `LOW` | `089_taobao_01_淘宝直播带货_v28` | 56 | 53 / 94.6% | 5.4% | 10.7% | 2 / 3.6% | 10.7% | 0.2% |
| `LOW` | `023_eleme_18_饿了么闪购_v28` | 56 | 54 / 96.4% | 3.6% | 7.1% | 2 / 3.6% | 8.9% | 0.1% |
| `LOW` | `049_meituan_01_外卖配送_v28` | 56 | 54 / 96.4% | 3.6% | 7.1% | 2 / 3.6% | 8.9% | 0.1% |
| `LOW` | `041_jingdong_10_延保服务申请_v28` | 56 | 55 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.1% | 0.1% |
| `LOW` | `062_meituan_14_美团众包骑手端_v28` | 56 | 55 / 98.2% | 1.8% | 3.6% | 2 / 3.6% | 7.1% | 0.1% |
| `LOW` | `054_meituan_07_美团单车_v28` | 57 | 53 / 93.0% | 7.0% | 14.0% | 2 / 3.5% | 10.5% | 0.3% |
| `LOW` | `056_meituan_08_美团打车_v28` | 58 | 56 / 96.6% | 3.4% | 6.9% | 2 / 3.4% | 8.6% | 0.1% |
| `LOW` | `052_meituan_05_美团优选_v28` | 52 | 52 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.8% | 0.0% |
| `LOW` | `123_03_public_library` | 52 | 52 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.8% | 0.0% |
| `LOW` | `128_08_coworking_room` | 52 | 52 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.8% | 0.0% |
| `LOW` | `129_09_lab_instrument` | 52 | 52 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.8% | 0.0% |
| `LOW` | `010_chain_restaurant_04_肯德基客服_v28` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `013_eleme_03_饿了么骑手端_v28` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `017_eleme_08_饿了么企业版_v28` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `073_payment_04_提现转账异常_v28` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `121_01_smart_locker` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `124_04_parking_pass` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `125_05_ev_charging` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `127_07_laundry_care` | 53 | 53 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.7% | 0.0% |
| `LOW` | `012_eleme_02_饿了么商家端_v28` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `024_insurance_01_保险报案受理流程_v28` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `029_insurance_06_互联网保险理赔_v28` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `031_insurance_11_保全服务流程_v28` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `051_meituan_04_美团买菜_v28` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `131_01_delivery_progress` | 54 | 54 / 100.0% | 0.0% | 0.0% | 1 / 1.9% | 5.6% | 0.0% |
| `LOW` | `007_chain_restaurant_01_麦当劳运营_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `011_eleme_01_饿了么外卖配送_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `020_eleme_11_饿了么买菜_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `038_jingdong_07_订单信息修改_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `072_payment_03_实名认证流程_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `085_pdd_15_省钱月卡_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `130_10_cloud_printing` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `132_06_jingdong_invoice_reissue_v28` | 55 | 55 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.5% | 0.0% |
| `LOW` | `018_eleme_09_饿了么营销优惠_v28` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `033_jingdong_01_七天无理由退货_v28` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `040_jingdong_09_取消订单_v28` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `067_meituan_22_美团企业版_v28` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `076_pdd_01_百亿补贴_v28` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `122_02_pet_clinic` | 56 | 56 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.4% | 0.0% |
| `LOW` | `014_eleme_04_饿了么买药_v28` | 57 | 57 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.3% | 0.0% |
| `LOW` | `022_eleme_16_饿了么评价管理_v28` | 57 | 57 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.3% | 0.0% |
| `LOW` | `079_pdd_04_多多买菜_v28` | 57 | 57 / 100.0% | 0.0% | 0.0% | 1 / 1.8% | 5.3% | 0.0% |
| `LOW` | `053_meituan_06_美团跑腿_v28` | 58 | 58 / 100.0% | 0.0% | 0.0% | 1 / 1.7% | 5.2% | 0.0% |
| `LOW` | `071_payment_02_交易纠纷处理_v28` | 58 | 58 / 100.0% | 0.0% | 0.0% | 1 / 1.7% | 5.2% | 0.0% |
| `LOW` | `126_06_fitness_class` | 58 | 58 / 100.0% | 0.0% | 0.0% | 1 / 1.7% | 5.2% | 0.0% |

### 全部完全重复组

#### `001_bank_01_信用卡申请审批流程_v28`

- Answer指纹 `40507ac99e0e`：3条；`018.json`、`025.json`、`050.json`
- Answer指纹 `4e9a8583ff08`：3条；`007.json`、`028.json`、`031.json`
- Answer指纹 `877da505161a`：3条；`001.json`、`029.json`、`046.json`
- Answer指纹 `93a79bf388bf`：3条；`006.json`、`037.json`、`054.json`
- Answer指纹 `dca57010f19d`：3条；`002.json`、`047.json`、`065.json`
- Answer指纹 `1215300293c6`：2条；`016.json`、`034.json`
- Answer指纹 `210aab039458`：2条；`005.json`、`043.json`
- Answer指纹 `2c3952e47a76`：2条；`026.json`、`042.json`
- Answer指纹 `45e98ac67a42`：2条；`010.json`、`044.json`
- Answer指纹 `4bf14c12ed0f`：2条；`021.json`、`032.json`
- Answer指纹 `54fe835ab5b5`：2条；`004.json`、`033.json`
- Answer指纹 `57606ef8f663`：2条；`023.json`、`051.json`
- Answer指纹 `94fdba5f6004`：2条；`009.json`、`040.json`
- Answer指纹 `a1db825b7c3e`：2条；`013.json`、`039.json`
- Answer指纹 `f16502f44ab4`：2条；`008.json`、`045.json`

#### `002_bank_02_挂失解挂流程_v28`

- Answer指纹 `914ec88e1c2f`：3条；`003.json`、`043.json`、`047.json`
- Answer指纹 `c43610d9c4bb`：2条；`014.json`、`050.json`

#### `003_bank_03_转账异常处理_v28`

- Answer指纹 `a48c6ea9987a`：4条；`014.json`、`034.json`、`053.json`、`054.json`
- Answer指纹 `055bd0fe7939`：2条；`036.json`、`049.json`
- Answer指纹 `767bc888630f`：2条；`027.json`、`051.json`
- Answer指纹 `7c6af4b5c979`：2条；`011.json`、`055.json`
- Answer指纹 `821bee2d911a`：2条；`022.json`、`046.json`
- Answer指纹 `8796d4a88481`：2条；`018.json`、`048.json`
- Answer指纹 `aa4996d7a8d5`：2条；`015.json`、`047.json`
- Answer指纹 `ab0397009c6a`：2条；`026.json`、`063.json`
- Answer指纹 `d8b402b69640`：2条；`024.json`、`060.json`
- Answer指纹 `e0d68cc3cfc8`：2条；`028.json`、`065.json`
- Answer指纹 `e48ee266412a`：2条；`010.json`、`050.json`

#### `004_bank_04_贷款咨询与申请_v28`

- Answer指纹 `67132df8a78a`：3条；`025.json`、`038.json`、`044.json`
- Answer指纹 `13d4b093a7dc`：2条；`005.json`、`048.json`
- Answer指纹 `283c42a3e42d`：2条；`021.json`、`055.json`
- Answer指纹 `45711a57a44e`：2条；`029.json`、`047.json`
- Answer指纹 `4f82f782dc43`：2条；`001.json`、`068.json`
- Answer指纹 `a95d1aede754`：2条；`009.json`、`045.json`
- Answer指纹 `b54e76e65f80`：2条；`012.json`、`050.json`
- Answer指纹 `b72aa670f896`：2条；`006.json`、`040.json`
- Answer指纹 `d8e96168bee1`：2条；`019.json`、`043.json`

#### `005_bank_05_理财产品购买流程_v28`

- Answer指纹 `0057c3140cf4`：2条；`023.json`、`037.json`
- Answer指纹 `508ec7e4de02`：2条；`028.json`、`045.json`
- Answer指纹 `6d2d638569c0`：2条；`004.json`、`053.json`
- Answer指纹 `6f637096ba24`：2条；`032.json`、`048.json`
- Answer指纹 `d2403ccc3b8e`：2条；`010.json`、`054.json`
- Answer指纹 `f8300710dd64`：2条；`030.json`、`046.json`

#### `006_bank_06_投诉建议处理_v28`

- Answer指纹 `981de9c22346`：15条；`001.json`、`004.json`、`008.json`、`011.json`、`014.json`、`016.json`、`021.json`、`024.json`、`027.json`、`029.json`、`032.json`、`039.json`、`040.json`、`049.json`、`054.json`

#### `008_chain_restaurant_02_海底捞服务_v28`

- Answer指纹 `feafdc0f98c1`：5条；`006.json`、`017.json`、`023.json`、`046.json`、`048.json`
- Answer指纹 `6cb92ac94eca`：4条；`016.json`、`021.json`、`043.json`、`056.json`
- Answer指纹 `969487a2c9e6`：3条；`033.json`、`039.json`、`047.json`
- Answer指纹 `22a94725928b`：2条；`025.json`、`054.json`
- Answer指纹 `c89fd9f3b363`：2条；`036.json`、`045.json`
- Answer指纹 `e89139a840d5`：2条；`012.json`、`050.json`

#### `009_chain_restaurant_03_星巴克门店运营_v28`

- Answer指纹 `9af4bf53ca3a`：2条；`011.json`、`022.json`

#### `015_eleme_06_饿了么会员_v28`

- Answer指纹 `c57afd7baa74`：2条；`010.json`、`052.json`

#### `016_eleme_07_饿了么客服_v28`

- Answer指纹 `3267fb6fa1ae`：2条；`036.json`、`060.json`
- Answer指纹 `3fdf80c530b5`：2条；`026.json`、`065.json`

#### `019_eleme_10_饿了么物流管理_v28`

- Answer指纹 `c4c41b2a27f6`：11条；`002.json`、`005.json`、`010.json`、`013.json`、`024.json`、`028.json`、`033.json`、`035.json`、`044.json`、`051.json`、`054.json`
- Answer指纹 `8666cd925ece`：5条；`004.json`、`009.json`、`025.json`、`031.json`、`039.json`
- Answer指纹 `500282771504`：3条；`018.json`、`037.json`、`048.json`
- Answer指纹 `a4272cf20729`：2条；`020.json`、`043.json`

#### `021_eleme_13_饿了么跑腿_v28`

- Answer指纹 `ebc52948dda3`：3条；`030.json`、`045.json`、`049.json`
- Answer指纹 `0f4551e42754`：2条；`006.json`、`055.json`
- Answer指纹 `275ea2ca1a3b`：2条；`023.json`、`046.json`
- Answer指纹 `30535e6ee525`：2条；`011.json`、`050.json`
- Answer指纹 `3c73473e108f`：2条；`009.json`、`054.json`
- Answer指纹 `5dab12430d58`：2条；`021.json`、`048.json`
- Answer指纹 `b4976db63ad2`：2条；`016.json`、`047.json`
- Answer指纹 `b8fbefa2cc42`：2条；`040.json`、`063.json`
- Answer指纹 `fcbd058bddc8`：2条；`018.json`、`060.json`

#### `023_eleme_18_饿了么闪购_v28`

- Answer指纹 `0a37627e9d1c`：2条；`039.json`、`063.json`
- Answer指纹 `a1678c6b5b85`：2条；`023.json`、`060.json`

#### `025_insurance_02_理赔资料审核流程_v28`

- Answer指纹 `4c59dbe8481a`：2条；`035.json`、`063.json`

#### `026_insurance_03_保单变更流程_v28`

- Answer指纹 `41e36820d3ce`：9条；`004.json`、`006.json`、`015.json`、`016.json`、`030.json`、`035.json`、`038.json`、`049.json`、`065.json`
- Answer指纹 `32d64ae50b05`：2条；`014.json`、`051.json`
- Answer指纹 `e8d73cadd887`：2条；`005.json`、`031.json`

#### `027_insurance_04_退保处理流程_v28`

- Answer指纹 `f91e9aea1edc`：3条；`026.json`、`035.json`、`060.json`
- Answer指纹 `1fc38876a194`：2条；`008.json`、`037.json`
- Answer指纹 `4db099a307dc`：2条；`025.json`、`044.json`
- Answer指纹 `5961a65b7652`：2条；`016.json`、`040.json`
- Answer指纹 `6bfe76598ebd`：2条；`013.json`、`046.json`
- Answer指纹 `b885174a0e92`：2条；`012.json`、`052.json`

#### `028_insurance_05_保险客户投诉处理_v28`

- Answer指纹 `981de9c22346`：17条；`001.json`、`004.json`、`008.json`、`011.json`、`013.json`、`018.json`、`023.json`、`027.json`、`030.json`、`032.json`、`036.json`、`039.json`、`040.json`、`045.json`、`049.json`、`056.json`、`060.json`

#### `030_insurance_07_查勘定损流程_v28`

- Answer指纹 `0af05ed1aebc`：2条；`015.json`、`065.json`

#### `032_insurance_12_反欺诈调查流程_v28`

- Answer指纹 `5a085460fe65`：2条；`035.json`、`051.json`
- Answer指纹 `97625421b22e`：2条；`012.json`、`048.json`
- Answer指纹 `98340086bb7b`：2条；`019.json`、`049.json`
- Answer指纹 `a52b4dfc173d`：2条；`024.json`、`050.json`
- Answer指纹 `d5e7944e473f`：2条；`034.json`、`056.json`
- Answer指纹 `dc13b97b376c`：2条；`008.json`、`055.json`

#### `034_jingdong_02_商品质量问题退货_v28`

- Answer指纹 `2e9b3efdc5b8`：2条；`020.json`、`057.json`
- Answer指纹 `3e5a4e900675`：2条；`009.json`、`034.json`
- Answer指纹 `4110dc1657a1`：2条；`007.json`、`047.json`
- Answer指纹 `4567a8e4b4a3`：2条；`024.json`、`063.json`
- Answer指纹 `4d1c0251678f`：2条；`002.json`、`046.json`
- Answer指纹 `580543c80dac`：2条；`023.json`、`042.json`
- Answer指纹 `58aeb1eb2448`：2条；`006.json`、`051.json`
- Answer指纹 `596dbabd3812`：2条；`027.json`、`040.json`
- Answer指纹 `626cab80ccae`：2条；`015.json`、`041.json`
- Answer指纹 `6f6bb52a2c8e`：2条；`022.json`、`053.json`
- Answer指纹 `6fca3007f9e0`：2条；`014.json`、`049.json`
- Answer指纹 `7785ca46038e`：2条；`016.json`、`045.json`
- Answer指纹 `898114d814f8`：2条；`005.json`、`068.json`
- Answer指纹 `b9092c9588df`：2条；`013.json`、`035.json`
- Answer指纹 `cf37d3d7b2e9`：2条；`026.json`、`050.json`
- Answer指纹 `d89da3a7b5d9`：2条；`003.json`、`044.json`
- Answer指纹 `eb6c347be50b`：2条；`019.json`、`036.json`

#### `035_jingdong_03_换货补发处理_v28`

- Answer指纹 `0887e2b2c8cf`：2条；`055.json`、`065.json`
- Answer指纹 `e7cca252b36f`：2条；`033.json`、`057.json`

#### `036_jingdong_04_仅退款不退货_v28`

- Answer指纹 `0d77713d1124`：2条；`012.json`、`053.json`
- Answer指纹 `129e0cdadde3`：2条；`028.json`、`033.json`
- Answer指纹 `23c157751642`：2条；`035.json`、`046.json`
- Answer指纹 `253e649ed9c6`：2条；`005.json`、`050.json`
- Answer指纹 `30c7deb638dd`：2条；`022.json`、`043.json`
- Answer指纹 `5846e29fb2dc`：2条；`029.json`、`047.json`
- Answer指纹 `5dfd5e61d787`：2条；`010.json`、`060.json`
- Answer指纹 `5e3699ad7f16`：2条；`013.json`、`044.json`
- Answer指纹 `729d5ffe8e41`：2条；`009.json`、`057.json`
- Answer指纹 `7c0c4d46ad04`：2条；`017.json`、`042.json`
- Answer指纹 `964d915fd276`：2条；`011.json`、`041.json`
- Answer指纹 `c76a5a2a70cf`：2条；`014.json`、`048.json`
- Answer指纹 `ce970ea2eb59`：2条；`016.json`、`065.json`
- Answer指纹 `d41a030258f4`：2条；`015.json`、`039.json`
- Answer指纹 `d4dc9b100de9`：2条；`004.json`、`040.json`

#### `037_jingdong_05_30天价保申请_v28`

- Answer指纹 `7aba2d745723`：5条；`008.json`、`020.json`、`034.json`、`046.json`、`068.json`
- Answer指纹 `4d393d9d7575`：2条；`019.json`、`042.json`

#### `039_jingdong_08_物流异常处理_v28`

- Answer指纹 `049c90cbe635`：2条；`006.json`、`057.json`
- Answer指纹 `64bfc2e28adc`：2条；`023.json`、`047.json`
- Answer指纹 `81499a20213a`：2条；`018.json`、`054.json`
- Answer指纹 `832b7391badd`：2条；`030.json`、`050.json`
- Answer指纹 `b25aa9ac9517`：2条；`002.json`、`005.json`
- Answer指纹 `b918249da8cc`：2条；`026.json`、`068.json`

#### `041_jingdong_10_延保服务申请_v28`

- Answer指纹 `08ebdc72e14b`：2条；`027.json`、`065.json`

#### `042_jingdong_11_用户投诉处理_v28`

- Answer指纹 `028d732a934d`：2条；`003.json`、`060.json`
- Answer指纹 `1800ea0e19ad`：2条；`008.json`、`068.json`
- Answer指纹 `5c8f9b7e4717`：2条；`016.json`、`046.json`
- Answer指纹 `898858e20c9d`：2条；`018.json`、`056.json`
- Answer指纹 `b03a4df39ef5`：2条；`021.json`、`049.json`
- Answer指纹 `d6bb39abc64a`：2条；`011.json`、`048.json`

#### `043_jingdong_12_白条分期问题_v28`

- Answer指纹 `0385ebfd0bcf`：2条；`040.json`、`047.json`
- Answer指纹 `96f98a4cf58c`：2条；`029.json`、`054.json`
- Answer指纹 `9f34940e56a0`：2条；`013.json`、`043.json`
- Answer指纹 `b5e182b54f01`：2条；`012.json`、`044.json`
- Answer指纹 `ba2240a89a82`：2条；`004.json`、`048.json`

#### `044_jingdong_13_以旧换新_v28`

- Answer指纹 `0e6084f786db`：2条；`035.json`、`053.json`
- Answer指纹 `1047afe89900`：2条；`025.json`、`052.json`
- Answer指纹 `57fcfb8a4790`：2条；`006.json`、`054.json`
- Answer指纹 `85b6e580b347`：2条；`045.json`、`048.json`
- Answer指纹 `a8ac1bdfc481`：2条；`003.json`、`050.json`
- Answer指纹 `cc9d6635fea7`：2条；`019.json`、`049.json`

#### `045_jingdong_14_京东服务__v28`

- Answer指纹 `30d1c12bc73c`：2条；`035.json`、`055.json`
- Answer指纹 `423bf845cdd2`：2条；`013.json`、`057.json`
- Answer指纹 `d43b26676bb4`：2条；`024.json`、`054.json`

#### `046_jingdong_16_企业购_v28`

- Answer指纹 `b6b8a1bf1ff1`：2条；`005.json`、`006.json`

#### `047_jingdong_17_账户被盗申诉处理_v28`

- Answer指纹 `47e708528e8a`：2条；`037.json`、`063.json`
- Answer指纹 `d98c2f841ef8`：2条；`007.json`、`065.json`

#### `048_jingdong_18_交易纠纷仲裁_v28`

- Answer指纹 `1c24eca3a06d`：2条；`011.json`、`055.json`
- Answer指纹 `7faa503e74d2`：2条；`031.json`、`045.json`
- Answer指纹 `d22444afaace`：2条；`026.json`、`046.json`
- Answer指纹 `f1ff10ba054f`：2条；`017.json`、`059.json`

#### `049_meituan_01_外卖配送_v28`

- Answer指纹 `0fa196a7325a`：2条；`015.json`、`054.json`
- Answer指纹 `b9ba264c931c`：2条；`025.json`、`056.json`

#### `050_meituan_03_酒店旅游_v28`

- Answer指纹 `1bbaf3ccb3d3`：9条；`004.json`、`005.json`、`011.json`、`016.json`、`024.json`、`032.json`、`034.json`、`036.json`、`039.json`
- Answer指纹 `fddd27c2b3d6`：4条；`003.json`、`014.json`、`052.json`、`059.json`
- Answer指纹 `f4d1a03a581c`：3条；`027.json`、`048.json`、`057.json`
- Answer指纹 `8c53924d1d0e`：2条；`019.json`、`056.json`
- Answer指纹 `c19f78d56b02`：2条；`006.json`、`022.json`

#### `054_meituan_07_美团单车_v28`

- Answer指纹 `1b0722a820b5`：2条；`028.json`、`059.json`
- Answer指纹 `91728471c5e1`：2条；`013.json`、`057.json`
- Answer指纹 `a40b0139c98b`：2条；`044.json`、`053.json`
- Answer指纹 `ba2907a4e39c`：2条；`005.json`、`054.json`

#### `055_meituan_08_美团外卖运营_v28`

- Answer指纹 `f0ffd87a0373`：5条；`005.json`、`018.json`、`032.json`、`040.json`、`057.json`

#### `056_meituan_08_美团打车_v28`

- Answer指纹 `094c8caba593`：2条；`005.json`、`056.json`
- Answer指纹 `d70b1e048a38`：2条；`027.json`、`068.json`

#### `057_meituan_09_美团买药_v28`

- Answer指纹 `c4c38143e2b6`：2条；`034.json`、`060.json`

#### `058_meituan_10_美团充电宝_v28`

- Answer指纹 `db53405e0f06`：3条；`006.json`、`036.json`、`055.json`
- Answer指纹 `0f48126a10dc`：2条；`017.json`、`047.json`
- Answer指纹 `10eeebed875a`：2条；`021.json`、`040.json`
- Answer指纹 `1d2b44ff4072`：2条；`016.json`、`042.json`
- Answer指纹 `2d195e20de0e`：2条；`019.json`、`038.json`
- Answer指纹 `2e4175b30360`：2条；`013.json`、`057.json`
- Answer指纹 `36f4318d7449`：2条；`023.json`、`044.json`
- Answer指纹 `4ef8f370ac64`：2条；`003.json`、`048.json`
- Answer指纹 `5e9bb8ad54b2`：2条；`014.json`、`037.json`
- Answer指纹 `6bc86ce75e0f`：2条；`011.json`、`035.json`
- Answer指纹 `77833bcc35db`：2条；`004.json`、`046.json`
- Answer指纹 `785be329188c`：2条；`024.json`、`039.json`
- Answer指纹 `8ad8cd89ab0b`：2条；`005.json`、`056.json`
- Answer指纹 `8d8ec44cd422`：2条；`015.json`、`051.json`
- Answer指纹 `af632cee80e0`：2条；`012.json`、`063.json`
- Answer指纹 `d8df86fe5fd8`：2条；`032.json`、`045.json`
- Answer指纹 `dc33128afdd4`：2条；`031.json`、`050.json`
- Answer指纹 `f68ee161789d`：2条；`028.json`、`041.json`

#### `059_meituan_11_美团会员_v28`

- Answer指纹 `0accdae5e524`：2条；`017.json`、`025.json`

#### `060_meituan_12_美团客服_v28`

- Answer指纹 `2c216e87d745`：3条；`009.json`、`021.json`、`037.json`
- Answer指纹 `83159cff0098`：3条；`005.json`、`024.json`、`053.json`
- Answer指纹 `bc2ce6cadf8e`：3条；`015.json`、`029.json`、`060.json`
- Answer指纹 `befad2106778`：3条；`008.json`、`014.json`、`044.json`
- Answer指纹 `dbd0460cab22`：3条；`004.json`、`042.json`、`049.json`
- Answer指纹 `ddf83e46d941`：3条；`019.json`、`032.json`、`057.json`
- Answer指纹 `1b6ad079b9ae`：2条；`031.json`、`051.json`
- Answer指纹 `27b4615f9fe4`：2条；`007.json`、`030.json`
- Answer指纹 `52efb364fabb`：2条；`011.json`、`026.json`
- Answer指纹 `70398abced71`：2条；`020.json`、`041.json`
- Answer指纹 `790a1195a430`：2条；`006.json`、`025.json`
- Answer指纹 `9675c4e2a538`：2条；`022.json`、`050.json`
- Answer指纹 `a7ef1b96d635`：2条；`035.json`、`046.json`
- Answer指纹 `ab41a1cc11ef`：2条；`017.json`、`040.json`
- Answer指纹 `ae60182b97f0`：2条；`003.json`、`047.json`
- Answer指纹 `b14d2714efd8`：2条；`016.json`、`038.json`
- Answer指纹 `c155d485aff4`：2条；`012.json`、`023.json`

#### `061_meituan_13_美团外卖商家端_v28`

- Answer指纹 `0a987bf94ba6`：2条；`007.json`、`016.json`
- Answer指纹 `1f434059e22c`：2条；`015.json`、`040.json`
- Answer指纹 `4b977e4d131f`：2条；`009.json`、`037.json`
- Answer指纹 `d6110a2803ce`：2条；`026.json`、`046.json`

#### `062_meituan_14_美团众包骑手端_v28`

- Answer指纹 `8d63873a3f07`：2条；`004.json`、`026.json`

#### `063_meituan_15_美团闪购商家端_v28`

- Answer指纹 `351431388adf`：2条；`042.json`、`050.json`
- Answer指纹 `6d5d5bdbc99a`：2条；`017.json`、`037.json`

#### `064_meituan_16_美团闪购用户端_v28`

- Answer指纹 `5acd59b2fcd5`：2条；`021.json`、`047.json`
- Answer指纹 `6c3948ef5b7d`：2条；`026.json`、`050.json`
- Answer指纹 `a1d53ec2679a`：2条；`046.json`、`063.json`
- Answer指纹 `c9e1dc9be364`：2条；`020.json`、`059.json`

#### `065_meituan_17_美团民宿_v28`

- Answer指纹 `1974dcc6ce42`：2条；`015.json`、`047.json`
- Answer指纹 `1d3776c67b0e`：2条；`020.json`、`048.json`
- Answer指纹 `56a08cc36cc3`：2条；`032.json`、`065.json`
- Answer指纹 `64a5837a5924`：2条；`037.json`、`063.json`
- Answer指纹 `659dfb078240`：2条；`001.json`、`041.json`
- Answer指纹 `6ab5d3528fe9`：2条；`011.json`、`059.json`
- Answer指纹 `7b00f51f8686`：2条；`036.json`、`049.json`
- Answer指纹 `9f7dc7e7edb0`：2条；`038.json`、`050.json`
- Answer指纹 `c88a31d23316`：2条；`006.json`、`042.json`
- Answer指纹 `d7a6d5ea6f89`：2条；`039.json`、`057.json`
- Answer指纹 `d835760c276d`：2条；`012.json`、`043.json`
- Answer指纹 `dcc3890a6bc9`：2条；`017.json`、`044.json`
- Answer指纹 `e9fb9a03ea7d`：2条；`026.json`、`054.json`
- Answer指纹 `f02992e9a25f`：2条；`013.json`、`040.json`

#### `066_meituan_21_美团无人配送_v28`

- Answer指纹 `c6c3fb4ef404`：2条；`009.json`、`045.json`

#### `068_meituan_23_美团金融_v28`

- Answer指纹 `6a021b6c1dfd`：3条；`008.json`、`026.json`、`053.json`
- Answer指纹 `718995f67589`：3条；`015.json`、`045.json`、`057.json`
- Answer指纹 `7454c50ef42b`：3条；`021.json`、`029.json`、`051.json`
- Answer指纹 `7f5ae28095c2`：3条；`024.json`、`028.json`、`037.json`
- Answer指纹 `bc8e27def4f7`：3条；`001.json`、`030.json`、`047.json`
- Answer指纹 `d32444309d2e`：3条；`014.json`、`027.json`、`048.json`
- Answer指纹 `0b2251fae33b`：2条；`012.json`、`050.json`
- Answer指纹 `1612ed613a64`：2条；`016.json`、`034.json`
- Answer指纹 `493a2272d24e`：2条；`020.json`、`033.json`
- Answer指纹 `6e332099d17f`：2条；`002.json`、`039.json`
- Answer指纹 `721d62a4d94d`：2条；`022.json`、`035.json`
- Answer指纹 `a38133febf40`：2条；`004.json`、`055.json`
- Answer指纹 `bc8932afee63`：2条；`023.json`、`054.json`
- Answer指纹 `beb2ac87a476`：2条；`019.json`、`042.json`
- Answer指纹 `beed4ecc4192`：2条；`005.json`、`043.json`
- Answer指纹 `cda0d2e949e3`：2条；`009.json`、`046.json`
- Answer指纹 `e694b279609a`：2条；`010.json`、`041.json`
- Answer指纹 `fbafed9df3ca`：2条；`007.json`、`032.json`

#### `069_meituan_24_美团直播_v28`

- Answer指纹 `7e991d79f983`：9条；`004.json`、`010.json`、`013.json`、`022.json`、`023.json`、`027.json`、`033.json`、`047.json`、`063.json`
- Answer指纹 `0c908e65204c`：8条；`002.json`、`008.json`、`016.json`、`025.json`、`029.json`、`034.json`、`041.json`、`053.json`
- Answer指纹 `c1d7354548ae`：7条；`005.json`、`012.json`、`024.json`、`031.json`、`039.json`、`044.json`、`052.json`
- Answer指纹 `68f8fa4ee51d`：6条；`009.json`、`019.json`、`036.json`、`042.json`、`048.json`、`065.json`
- Answer指纹 `b1e2bfd146bf`：5条；`007.json`、`015.json`、`017.json`、`032.json`、`046.json`
- Answer指纹 `050e961cdc0c`：4条；`011.json`、`021.json`、`040.json`、`043.json`
- Answer指纹 `16f7d1ec0ac4`：2条；`049.json`、`056.json`
- Answer指纹 `264309855541`：2条；`014.json`、`026.json`
- Answer指纹 `4f3e55e53eb9`：2条；`037.json`、`045.json`
- Answer指纹 `771800ad343a`：2条；`038.json`、`059.json`

#### `070_payment_01_账户被盗申诉流程_v28`

- Answer指纹 `1635414507c0`：2条；`051.json`、`063.json`

#### `074_payment_05_商家退款流程_v28`

- Answer指纹 `260a06f48f3d`：2条；`041.json`、`065.json`
- Answer指纹 `8ff93012e788`：2条；`030.json`、`063.json`
- Answer指纹 `ab87598a21ed`：2条；`035.json`、`055.json`

#### `075_payment_06_支付风控解冻_v28`

- Answer指纹 `f5aac099b5f6`：4条；`002.json`、`008.json`、`021.json`、`039.json`
- Answer指纹 `16910b191b55`：3条；`027.json`、`038.json`、`043.json`
- Answer指纹 `28979c486ec1`：3条；`010.json`、`037.json`、`048.json`
- Answer指纹 `4a8fcb60a7a7`：3条；`005.json`、`026.json`、`044.json`
- Answer指纹 `5f4fe1470499`：3条；`009.json`、`031.json`、`042.json`
- Answer指纹 `703819e02e76`：3条；`022.json`、`056.json`、`068.json`
- Answer指纹 `82d67acdaf3a`：3条；`012.json`、`030.json`、`046.json`
- Answer指纹 `8b3042d8e0f5`：3条；`015.json`、`028.json`、`051.json`
- Answer指纹 `9180dcd0b755`：3条；`025.json`、`034.json`、`049.json`
- Answer指纹 `cb913c13db5e`：3条；`003.json`、`014.json`、`053.json`
- Answer指纹 `1b7f9f1425c8`：2条；`019.json`、`041.json`
- Answer指纹 `261fd46b8586`：2条；`004.json`、`013.json`
- Answer指纹 `609d2aae5d08`：2条；`011.json`、`057.json`
- Answer指纹 `682afdb646ee`：2条；`024.json`、`045.json`
- Answer指纹 `a28eb24d92e6`：2条；`020.json`、`055.json`

#### `077_pdd_02_拼团模式_v28`

- Answer指纹 `f89d37fb2d2b`：2条；`045.json`、`068.json`

#### `078_pdd_03_农产品生鲜_v28`

- Answer指纹 `0dc3ce828c7a`：2条；`022.json`、`059.json`

#### `080_pdd_06_多多进宝_v28`

- Answer指纹 `187ecae116a5`：4条；`003.json`、`011.json`、`035.json`、`051.json`
- Answer指纹 `39bb2218e64e`：3条；`002.json`、`032.json`、`065.json`
- Answer指纹 `4af6c17135f2`：3条；`028.json`、`044.json`、`059.json`
- Answer指纹 `5a3f227af175`：3条；`015.json`、`026.json`、`043.json`
- Answer指纹 `d68813baf7c2`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `0a02e2245f9b`：2条；`013.json`、`037.json`
- Answer指纹 `1b79f40b14e9`：2条；`024.json`、`029.json`
- Answer指纹 `24f061627e69`：2条；`016.json`、`036.json`
- Answer指纹 `28382d51f009`：2条；`006.json`、`047.json`
- Answer指纹 `2d3e3030fdd0`：2条；`019.json`、`039.json`
- Answer指纹 `31db2a5cf245`：2条；`023.json`、`038.json`
- Answer指纹 `37e68dbf428d`：2条；`021.json`、`055.json`
- Answer指纹 `51fb7de9e295`：2条；`022.json`、`040.json`
- Answer指纹 `53e93c4052c9`：2条；`012.json`、`050.json`
- Answer指纹 `6154e9f7bb1d`：2条；`010.json`、`049.json`
- Answer指纹 `671cf1591b76`：2条；`025.json`、`045.json`
- Answer指纹 `6acc9f6edb71`：2条；`020.json`、`057.json`
- Answer指纹 `9ccd62d45ee0`：2条；`001.json`、`053.json`
- Answer指纹 `b1f02aa9e88f`：2条；`007.json`、`034.json`
- Answer指纹 `b783914286d0`：2条；`005.json`、`046.json`
- Answer指纹 `b94803f617c3`：2条；`004.json`、`041.json`
- Answer指纹 `bb1216b46480`：2条；`031.json`、`063.json`
- Answer指纹 `de0ff98e3d68`：2条；`008.json`、`054.json`
- Answer指纹 `ec00363315a7`：2条；`017.json`、`042.json`

#### `081_pdd_07_多多直播_v28`

- Answer指纹 `1ae78c9661f5`：3条；`002.json`、`031.json`、`060.json`
- Answer指纹 `4db13570e8e3`：3条；`024.json`、`045.json`、`068.json`
- Answer指纹 `58d7b99fc999`：3条；`019.json`、`022.json`、`035.json`
- Answer指纹 `87e8f34597b0`：3条；`017.json`、`038.json`、`056.json`
- Answer指纹 `a65ba3344e61`：3条；`008.json`、`030.json`、`039.json`
- Answer指纹 `3997391bb02c`：2条；`010.json`、`032.json`
- Answer指纹 `73846e36a154`：2条；`011.json`、`044.json`
- Answer指纹 `c8bf4d4d6a60`：2条；`006.json`、`025.json`
- Answer指纹 `d8a66b5438a3`：2条；`016.json`、`059.json`
- Answer指纹 `ec79cec2a6f7`：2条；`036.json`、`042.json`

#### `082_pdd_09_多多国际_v28`

- Answer指纹 `81359fc870ce`：4条；`004.json`、`014.json`、`021.json`、`041.json`
- Answer指纹 `155d9f965979`：2条；`023.json`、`046.json`
- Answer指纹 `f6e91745082b`：2条；`018.json`、`028.json`

#### `083_pdd_10_假一赔十_v28`

- Answer指纹 `2b204718834f`：2条；`001.json`、`053.json`
- Answer指纹 `2e848819348c`：2条；`019.json`、`047.json`
- Answer指纹 `32a686519c30`：2条；`031.json`、`050.json`
- Answer指纹 `4509f47d2e7d`：2条；`005.json`、`065.json`
- Answer指纹 `a65221afe794`：2条；`017.json`、`054.json`
- Answer指纹 `da2947ad7ae1`：2条；`016.json`、`051.json`

#### `084_pdd_13_砍价免费拿_v28`

- Answer指纹 `ec7480a623a6`：2条；`004.json`、`036.json`

#### `086_pdd_17_多多批发_v28`

- Answer指纹 `ce44a9ae01dc`：4条；`003.json`、`018.json`、`047.json`、`051.json`
- Answer指纹 `1faf5a7b172a`：2条；`020.json`、`057.json`
- Answer指纹 `2f4ac4ecfe82`：2条；`002.json`、`032.json`
- Answer指纹 `3853b648fefa`：2条；`017.json`、`042.json`
- Answer指纹 `5bf4c72f0df8`：2条；`011.json`、`035.json`
- Answer指纹 `6419991ee74b`：2条；`024.json`、`029.json`
- Answer指纹 `6636b0c8fc99`：2条；`027.json`、`033.json`
- Answer指纹 `8cfb74536362`：2条；`031.json`、`063.json`
- Answer指纹 `b3091f7a1e76`：2条；`013.json`、`037.json`
- Answer指纹 `d4465d013ae2`：2条；`016.json`、`036.json`
- Answer指纹 `de8e61dfbedb`：2条；`015.json`、`043.json`
- Answer指纹 `f02f727308d4`：2条；`008.json`、`026.json`

#### `087_pdd_18_偏远地区包邮_v28`

- Answer指纹 `c8d51d501dc4`：2条；`044.json`、`050.json`

#### `088_pdd_20_多多爱消除_v28`

- Answer指纹 `fc9eefca44b6`：3条；`002.json`、`039.json`、`040.json`
- Answer指纹 `34a4278ce3af`：2条；`031.json`、`063.json`
- Answer指纹 `5e693d7d5bf5`：2条；`026.json`、`050.json`
- Answer指纹 `a3b3eb09292b`：2条；`029.json`、`042.json`
- Answer指纹 `d5863596fe66`：2条；`033.json`、`053.json`

#### `089_taobao_01_淘宝直播带货_v28`

- Answer指纹 `17705ccdf4e2`：2条；`047.json`、`068.json`
- Answer指纹 `43b47d74dac4`：2条；`033.json`、`063.json`
- Answer指纹 `4e335451aaa9`：2条；`018.json`、`065.json`

#### `090_taobao_02_闲鱼二手交易_v28`

- Answer指纹 `5cd007ffde6d`：3条；`017.json`、`018.json`、`044.json`

#### `091_taobao_07_淘宝联盟推广_v28`

- Answer指纹 `0ed61e985e8a`：3条；`002.json`、`047.json`、`053.json`
- Answer指纹 `61580906ca39`：3条；`007.json`、`017.json`、`036.json`
- Answer指纹 `db677ea9054f`：3条；`024.json`、`028.json`、`057.json`
- Answer指纹 `ed95a72b5f50`：3条；`006.json`、`031.json`、`054.json`
- Answer指纹 `1e537ce24172`：2条；`027.json`、`042.json`
- Answer指纹 `32ba3c0cd752`：2条；`034.json`、`051.json`
- Answer指纹 `42d253361893`：2条；`033.json`、`044.json`
- Answer指纹 `530091dab4ef`：2条；`008.json`、`029.json`
- Answer指纹 `8984dedf93dd`：2条；`004.json`、`055.json`
- Answer指纹 `9d91d1d41ea4`：2条；`020.json`、`043.json`
- Answer指纹 `a33a25876b4f`：2条；`023.json`、`026.json`
- Answer指纹 `bed7d425b317`：2条；`032.json`、`059.json`
- Answer指纹 `de4c392e1caa`：2条；`016.json`、`040.json`
- Answer指纹 `f905236cbe55`：2条；`013.json`、`039.json`

#### `092_taobao_08_discount_v28`

- Answer指纹 `55a32841f142`：3条；`019.json`、`025.json`、`028.json`

#### `093_taobao_10_千牛商家服务_v28`

- Answer指纹 `3a7b94b78b25`：2条；`005.json`、`057.json`
- Answer指纹 `91de16f1e769`：2条；`034.json`、`048.json`
- Answer指纹 `e6458b241a97`：2条；`007.json`、`050.json`
- Answer指纹 `ff4152333099`：2条；`010.json`、`022.json`

#### `094_taobao_12_campaign_v28`

- Answer指纹 `63be4dc177d7`：2条；`017.json`、`022.json`

#### `095_taobao_14_淘宝租赁_v28`

- Answer指纹 `34cae6c8a8d9`：2条；`009.json`、`047.json`
- Answer指纹 `7a240e27e150`：2条；`041.json`、`065.json`
- Answer指纹 `92201e6a9e33`：2条；`046.json`、`059.json`

#### `096_taobao_15_天猫奢品_v28`

- Answer指纹 `8730f1b396f0`：2条；`033.json`、`057.json`
- Answer指纹 `a455cd0870dd`：2条；`007.json`、`065.json`

#### `097_telecom_01_中国移动客服_v28`

- Answer指纹 `7347a1609409`：7条；`007.json`、`009.json`、`021.json`、`026.json`、`034.json`、`041.json`、`049.json`
- Answer指纹 `d45e02932bbe`：3条；`010.json`、`037.json`、`051.json`
- Answer指纹 `00e37e47b837`：2条；`015.json`、`050.json`

#### `098_telecom_02_中国联通客服_v28`

- Answer指纹 `6575a9207099`：2条；`032.json`、`044.json`

#### `099_telecom_03_中国电信客服_v28`

- Answer指纹 `12629e2557fd`：3条；`009.json`、`028.json`、`059.json`

#### `100_01_reusable_container`

- Answer指纹 `8488c62df2cf`：3条；`003.json`、`018.json`、`051.json`
- Answer指纹 `117a3749b6b3`：2条；`004.json`、`041.json`
- Answer指纹 `27a82809192e`：2条；`017.json`、`042.json`
- Answer指纹 `27b792d8c806`：2条；`002.json`、`032.json`
- Answer指纹 `350307ecce0a`：2条；`015.json`、`043.json`
- Answer指纹 `3d4e9d8db9ed`：2条；`011.json`、`035.json`
- Answer指纹 `463206b6df17`：2条；`024.json`、`029.json`
- Answer指纹 `5f88911d740d`：2条；`019.json`、`039.json`
- Answer指纹 `73a2754b070c`：2条；`009.json`、`048.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `a8179b83a040`：2条；`020.json`、`057.json`
- Answer指纹 `ad499107936e`：2条；`010.json`、`049.json`
- Answer指纹 `c3c3d0fab55f`：2条；`025.json`、`045.json`
- Answer指纹 `cba4c45414ee`：2条；`016.json`、`036.json`
- Answer指纹 `d44741e6655c`：2条；`007.json`、`034.json`
- Answer指纹 `d66726cb8a88`：2条；`013.json`、`037.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `e328e81fb90e`：2条；`022.json`、`040.json`
- Answer指纹 `eef7addcdc35`：2条；`008.json`、`026.json`
- Answer指纹 `f12d7204ad4e`：2条；`012.json`、`050.json`
- Answer指纹 `f2bb569e5d70`：2条；`005.json`、`046.json`
- Answer指纹 `f9e83fd01855`：2条；`023.json`、`038.json`

#### `101_02_cold_storage_flex_load`

- Answer指纹 `0881d26ce570`：3条；`003.json`、`044.json`、`051.json`
- Answer指纹 `0a7455601f79`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `a19711f7c1d6`：3条；`008.json`、`026.json`、`054.json`
- Answer指纹 `09e4191bf65b`：2条；`017.json`、`042.json`
- Answer指纹 `2478c2519686`：2条；`010.json`、`049.json`
- Answer指纹 `3f6b8a2bda35`：2条；`012.json`、`050.json`
- Answer指纹 `4b20a82e750a`：2条；`019.json`、`039.json`
- Answer指纹 `4cb28dfdcbed`：2条；`022.json`、`040.json`
- Answer指纹 `4d91e07dea6c`：2条；`020.json`、`057.json`
- Answer指纹 `57ecd2102a26`：2条；`013.json`、`037.json`
- Answer指纹 `60487575b30c`：2条；`023.json`、`038.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `96734b25200d`：2条；`002.json`、`032.json`
- Answer指纹 `af1279a9d028`：2条；`021.json`、`055.json`
- Answer指纹 `b47ec5bcb4c1`：2条；`016.json`、`036.json`
- Answer指纹 `b5139d89a96a`：2条；`005.json`、`046.json`
- Answer指纹 `b786aa476c91`：2条；`007.json`、`034.json`
- Answer指纹 `c0eb575b6a67`：2条；`015.json`、`043.json`
- Answer指纹 `d41a02a03f45`：2条；`011.json`、`035.json`
- Answer指纹 `d55ed8e1b335`：2条；`004.json`、`041.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `e76ca078fc7d`：2条；`025.json`、`045.json`
- Answer指纹 `f49a13a3c968`：2条；`024.json`、`029.json`

#### `102_03_city_museum_pass`

- Answer指纹 `66d94b261a77`：3条；`002.json`、`032.json`、`065.json`
- Answer指纹 `b401500a2465`：3条；`006.json`、`015.json`、`043.json`
- Answer指纹 `b76c826d59a2`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `24843208c0b9`：2条；`003.json`、`051.json`
- Answer指纹 `312efb2ea8bc`：2条；`013.json`、`037.json`
- Answer指纹 `3237345c9906`：2条；`019.json`、`039.json`
- Answer指纹 `570394809885`：2条；`023.json`、`038.json`
- Answer指纹 `5b57a36826f5`：2条；`022.json`、`040.json`
- Answer指纹 `5e31dcee6696`：2条；`016.json`、`036.json`
- Answer指纹 `659c5b61ff47`：2条；`024.json`、`029.json`
- Answer指纹 `80f2be5a894c`：2条；`008.json`、`026.json`
- Answer指纹 `852cbaff7edb`：2条；`012.json`、`050.json`
- Answer指纹 `86a495ad2838`：2条；`010.json`、`049.json`
- Answer指纹 `90220e5c3285`：2条；`025.json`、`045.json`
- Answer指纹 `951cb205a312`：2条；`007.json`、`034.json`
- Answer指纹 `9e5b128fea75`：2条；`001.json`、`053.json`
- Answer指纹 `a056cddbfa7f`：2条；`017.json`、`042.json`
- Answer指纹 `da5e03607dde`：2条；`020.json`、`057.json`
- Answer指纹 `dc9a80e23664`：2条；`005.json`、`046.json`
- Answer指纹 `eb961ab441a6`：2条；`004.json`、`041.json`

#### `103_04_fleet_maintenance`

- Answer指纹 `6fef0c930adf`：3条；`004.json`、`018.json`、`041.json`
- Answer指纹 `88c668058871`：3条；`002.json`、`032.json`、`065.json`
- Answer指纹 `0a16fc780a02`：2条；`012.json`、`050.json`
- Answer指纹 `2a9aad72e380`：2条；`013.json`、`037.json`
- Answer指纹 `36569939df3b`：2条；`011.json`、`035.json`
- Answer指纹 `52154f04a396`：2条；`020.json`、`057.json`
- Answer指纹 `6b2082c82ab0`：2条；`017.json`、`042.json`
- Answer指纹 `73db2fa8b7d7`：2条；`016.json`、`036.json`
- Answer指纹 `7d12dfaa9e23`：2条；`022.json`、`040.json`
- Answer指纹 `8dd890b6075c`：2条；`026.json`、`028.json`
- Answer指纹 `938e86d584b5`：2条；`007.json`、`034.json`
- Answer指纹 `9573605293a8`：2条；`009.json`、`048.json`
- Answer指纹 `997aae8e1074`：2条；`019.json`、`039.json`
- Answer指纹 `9dafcfbe721e`：2条；`010.json`、`049.json`
- Answer指纹 `ba15183cda45`：2条；`024.json`、`029.json`
- Answer指纹 `c35a08c0d159`：2条；`003.json`、`051.json`
- Answer指纹 `caae3af07a97`：2条；`023.json`、`038.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `e4b3b33efd1b`：2条；`025.json`、`045.json`
- Answer指纹 `eeebd38a532d`：2条；`005.json`、`046.json`

#### `104_05_corporate_fitness_pass`

- Answer指纹 `e34148f01b44`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `07a4757bfdcf`：2条；`023.json`、`038.json`
- Answer指纹 `110722ed6395`：2条；`012.json`、`050.json`
- Answer指纹 `1563e99772c7`：2条；`007.json`、`034.json`
- Answer指纹 `21fe8b2d49e5`：2条；`025.json`、`045.json`
- Answer指纹 `233e1a89617b`：2条；`004.json`、`041.json`
- Answer指纹 `2aab68b4293c`：2条；`020.json`、`057.json`
- Answer指纹 `3c5528058427`：2条；`017.json`、`042.json`
- Answer指纹 `3cd60f44ccc0`：2条；`014.json`、`031.json`
- Answer指纹 `44f3b79ef9cd`：2条；`016.json`、`036.json`
- Answer指纹 `4826a4c4d5eb`：2条；`022.json`、`040.json`
- Answer指纹 `4a8b3b7006ac`：2条；`005.json`、`046.json`
- Answer指纹 `5adaf2541dc4`：2条；`002.json`、`032.json`
- Answer指纹 `7265fd361679`：2条；`024.json`、`029.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `9442d186ffec`：2条；`019.json`、`039.json`
- Answer指纹 `a550f1b6459d`：2条；`008.json`、`054.json`
- Answer指纹 `b7b8103a4791`：2条；`011.json`、`035.json`
- Answer指纹 `ba28d7efbbe3`：2条；`013.json`、`037.json`
- Answer指纹 `cb2582bef9c0`：2条；`010.json`、`049.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`

#### `105_06_corporate_dental_screening`

- Answer指纹 `153fbda315db`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `00cc33fd96bb`：2条；`012.json`、`050.json`
- Answer指纹 `3cc83163a946`：2条；`004.json`、`041.json`
- Answer指纹 `45e4a12b66db`：2条；`005.json`、`046.json`
- Answer指纹 `560bea35ca28`：2条；`008.json`、`054.json`
- Answer指纹 `575c7d8c1026`：2条；`011.json`、`035.json`
- Answer指纹 `57991e545142`：2条；`024.json`、`029.json`
- Answer指纹 `628da3a7bb1e`：2条；`016.json`、`036.json`
- Answer指纹 `661786bd032a`：2条；`010.json`、`049.json`
- Answer指纹 `69dada6d12e9`：2条；`023.json`、`038.json`
- Answer指纹 `6b8d184d5a85`：2条；`002.json`、`032.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `872f3a0f46a6`：2条；`003.json`、`051.json`
- Answer指纹 `9f8b8a5ca8b5`：2条；`025.json`、`045.json`
- Answer指纹 `af1279a9d028`：2条；`021.json`、`055.json`
- Answer指纹 `b78b466f0b70`：2条；`022.json`、`040.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `dd3992f055b1`：2条；`007.json`、`034.json`
- Answer指纹 `e3532ad9e057`：2条；`019.json`、`039.json`
- Answer指纹 `e45839e3e7fb`：2条；`017.json`、`042.json`
- Answer指纹 `eac9458061f5`：2条；`013.json`、`037.json`

#### `106_07_night_reading_bookstore`

- Answer指纹 `66012b386f65`：3条；`002.json`、`032.json`、`065.json`
- Answer指纹 `67773cb1a18b`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `eb27a894958a`：3条；`008.json`、`026.json`、`054.json`
- Answer指纹 `1241b65ffb98`：2条；`011.json`、`035.json`
- Answer指纹 `396cffd865eb`：2条；`020.json`、`057.json`
- Answer指纹 `3c8825bef0c1`：2条；`031.json`、`063.json`
- Answer指纹 `76d84eeb78b2`：2条；`014.json`、`056.json`
- Answer指纹 `7c3ef5ed9f6e`：2条；`010.json`、`049.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `8400f7b14783`：2条；`022.json`、`040.json`
- Answer指纹 `860426f8346c`：2条；`016.json`、`036.json`
- Answer指纹 `8dd890b6075c`：2条；`028.json`、`059.json`
- Answer指纹 `8e4f9c641155`：2条；`025.json`、`045.json`
- Answer指纹 `9033c7a2a8f7`：2条；`023.json`、`038.json`
- Answer指纹 `9220cb5c9bac`：2条；`004.json`、`041.json`
- Answer指纹 `9bd7eb99cf91`：2条；`012.json`、`050.json`
- Answer指纹 `a210b071ae3c`：2条；`005.json`、`046.json`
- Answer指纹 `a569d326b464`：2条；`019.json`、`039.json`
- Answer指纹 `b6ab794c9c0a`：2条；`013.json`、`037.json`
- Answer指纹 `bb3ac2e09360`：2条；`017.json`、`042.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `eef6f51782aa`：2条；`024.json`、`029.json`
- Answer指纹 `ff80186b29ff`：2条；`007.json`、`034.json`

#### `107_08_dorm_linen_care`

- Answer指纹 `0109aecabedd`：2条；`007.json`、`034.json`
- Answer指纹 `0c75bef31714`：2条；`025.json`、`045.json`
- Answer指纹 `171434115f71`：2条；`011.json`、`035.json`
- Answer指纹 `24a52a63a5dc`：2条；`024.json`、`029.json`
- Answer指纹 `32e8d46367c5`：2条；`009.json`、`048.json`
- Answer指纹 `36bd16430210`：2条；`015.json`、`043.json`
- Answer指纹 `3f0e673b5ecb`：2条；`022.json`、`040.json`
- Answer指纹 `50b4eaff7c50`：2条；`016.json`、`036.json`
- Answer指纹 `53366d3e109d`：2条；`005.json`、`046.json`
- Answer指纹 `67c1774d2d37`：2条；`019.json`、`039.json`
- Answer指纹 `786e6200f653`：2条；`012.json`、`050.json`
- Answer指纹 `7c87197c5a01`：2条；`023.json`、`038.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `844c97c6d68c`：2条；`014.json`、`068.json`
- Answer指纹 `a08f75029899`：2条；`008.json`、`026.json`
- Answer指纹 `a259f0c5aa10`：2条；`010.json`、`049.json`
- Answer指纹 `af1279a9d028`：2条；`021.json`、`055.json`
- Answer指纹 `c18beac53ca7`：2条；`002.json`、`032.json`
- Answer指纹 `c67cb901a19c`：2条；`013.json`、`037.json`
- Answer指纹 `d9a63f685d13`：2条；`004.json`、`041.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `f6c701cd4dea`：2条；`017.json`、`042.json`

#### `108_09_it_asset_recovery`

- Answer指纹 `0019ad0afdbd`：4条；`009.json`、`043.json`、`048.json`、`060.json`
- Answer指纹 `82503a432794`：3条；`011.json`、`018.json`、`035.json`
- Answer指纹 `8ce71add4690`：3条；`008.json`、`026.json`、`054.json`
- Answer指纹 `13b4aec721a8`：2条；`003.json`、`051.json`
- Answer指纹 `2a89402cba48`：2条；`001.json`、`053.json`
- Answer指纹 `462ec5efdf04`：2条；`024.json`、`029.json`
- Answer指纹 `48f464ac4812`：2条；`012.json`、`050.json`
- Answer指纹 `5ae250c7be3e`：2条；`005.json`、`046.json`
- Answer指纹 `6cbebe53cc64`：2条；`023.json`、`038.json`
- Answer指纹 `7672002b2a94`：2条；`013.json`、`037.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `8360995bbac8`：2条；`020.json`、`057.json`
- Answer指纹 `961852b07305`：2条；`017.json`、`042.json`
- Answer指纹 `af1279a9d028`：2条；`021.json`、`055.json`
- Answer指纹 `bc8f31d2980a`：2条；`002.json`、`032.json`
- Answer指纹 `c8d941b5fb1b`：2条；`010.json`、`049.json`
- Answer指纹 `d3cfbf520fad`：2条；`007.json`、`034.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `e41a7282cd39`：2条；`016.json`、`036.json`
- Answer指纹 `f42d7df4d852`：2条；`004.json`、`041.json`
- Answer指纹 `f4bdc51b6e29`：2条；`022.json`、`040.json`
- Answer指纹 `fbb62e04ec05`：2条；`019.json`、`039.json`
- Answer指纹 `fd87ff921230`：2条；`025.json`、`045.json`

#### `109_10_overflow_fulfillment`

- Answer指纹 `165d0c305cc7`：3条；`009.json`、`048.json`、`060.json`
- Answer指纹 `f17960eacb2c`：3条；`008.json`、`026.json`、`054.json`
- Answer指纹 `04a9405a0cb8`：2条；`019.json`、`039.json`
- Answer指纹 `15114b7ebc28`：2条；`010.json`、`049.json`
- Answer指纹 `1b186eec7e68`：2条；`002.json`、`032.json`
- Answer指纹 `2d4153dd7bf6`：2条；`022.json`、`040.json`
- Answer指纹 `315f3e41159b`：2条；`004.json`、`041.json`
- Answer指纹 `350307ecce0a`：2条；`015.json`、`043.json`
- Answer指纹 `44ebf0a3d6fc`：2条；`025.json`、`045.json`
- Answer指纹 `493c8b6b766c`：2条；`023.json`、`038.json`
- Answer指纹 `8112def7fc39`：2条；`006.json`、`047.json`
- Answer指纹 `83fba204865f`：2条；`007.json`、`034.json`
- Answer指纹 `92f32481091d`：2条；`017.json`、`042.json`
- Answer指纹 `94aa9c14ae0b`：2条；`016.json`、`036.json`
- Answer指纹 `98439ffd0d14`：2条；`001.json`、`053.json`
- Answer指纹 `af1279a9d028`：2条；`021.json`、`055.json`
- Answer指纹 `cafcfe970f06`：2条；`024.json`、`029.json`
- Answer指纹 `cbbac14f26a4`：2条；`003.json`、`051.json`
- Answer指纹 `d4ea562b29af`：2条；`012.json`、`050.json`
- Answer指纹 `da43f1972124`：2条；`027.json`、`033.json`
- Answer指纹 `db04992d3e0c`：2条；`014.json`、`056.json`
- Answer指纹 `e769a2a06c26`：2条；`011.json`、`035.json`
- Answer指纹 `eea2dfbf5f6b`：2条；`005.json`、`046.json`
- Answer指纹 `f0acb5efe73d`：2条；`013.json`、`037.json`

#### `110_01_piano_tuning`

- Answer指纹 `1e5f1815d10c`：3条；`013.json`、`029.json`、`055.json`
- Answer指纹 `626934a48df1`：3条；`019.json`、`043.json`、`050.json`
- Answer指纹 `910c8e58e1b1`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `b57d3343f4e7`：3条；`022.json`、`024.json`、`048.json`
- Answer指纹 `21111d98e1fa`：2条；`028.json`、`053.json`
- Answer指纹 `31c8118a7082`：2条；`023.json`、`047.json`
- Answer指纹 `39f4437fb740`：2条；`040.json`、`059.json`
- Answer指纹 `41dd35ba4332`：2条；`018.json`、`031.json`
- Answer指纹 `5f759fa3c748`：2条；`010.json`、`033.json`
- Answer指纹 `8ec2781972dc`：2条；`020.json`、`046.json`
- Answer指纹 `c69faa203dda`：2条；`026.json`、`045.json`
- Answer指纹 `ed03a52b5ec2`：2条；`008.json`、`038.json`
- Answer指纹 `eea86dee0b9f`：2条；`017.json`、`036.json`

#### `111_02_moving_estimate`

- Answer指纹 `272f74945a87`：4条；`012.json`、`025.json`、`041.json`、`063.json`
- Answer指纹 `13416c94023c`：3条；`022.json`、`024.json`、`048.json`
- Answer指纹 `47cd06fc96b5`：3条；`013.json`、`029.json`、`055.json`
- Answer指纹 `5f0b4642e588`：3条；`003.json`、`019.json`、`043.json`
- Answer指纹 `f8231ddfdc62`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `119ecfaa41ff`：2条；`023.json`、`047.json`
- Answer指纹 `15d117b8961e`：2条；`017.json`、`036.json`
- Answer指纹 `3a8621df946d`：2条；`001.json`、`039.json`
- Answer指纹 `577b7d3572f3`：2条；`018.json`、`031.json`
- Answer指纹 `6db3e3d5b3bf`：2条；`011.json`、`040.json`
- Answer指纹 `b21b87e66e42`：2条；`007.json`、`028.json`
- Answer指纹 `cc487057b594`：2条；`021.json`、`044.json`

#### `112_03_air_sampling`

- Answer指纹 `074822f345a6`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `228cb5a95866`：3条；`017.json`、`036.json`、`051.json`
- Answer指纹 `48f4984c1694`：3条；`008.json`、`038.json`、`057.json`
- Answer指纹 `862bd62edf80`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `cabf993ea23a`：3条；`013.json`、`029.json`、`055.json`
- Answer指纹 `dc071aea1da3`：3条；`001.json`、`039.json`、`056.json`
- Answer指纹 `2d2ccfaab7dc`：2条；`019.json`、`043.json`
- Answer指纹 `52f7d01a65ab`：2条；`018.json`、`031.json`
- Answer指纹 `80ff67883a44`：2条；`014.json`、`042.json`
- Answer指纹 `841963103406`：2条；`004.json`、`026.json`
- Answer指纹 `97289035c6c6`：2条；`023.json`、`047.json`
- Answer指纹 `b0a2e6b53d33`：2条；`024.json`、`048.json`
- Answer指纹 `c73a23a23e97`：2条；`010.json`、`033.json`
- Answer指纹 `e59821cba826`：2条；`007.json`、`053.json`

#### `113_04_office_plant_care`

- Answer指纹 `4e77f097e0b2`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `358337ffd101`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `aedee1127e6f`：3条；`008.json`、`038.json`、`057.json`
- Answer指纹 `d52e10c81cec`：3条；`022.json`、`024.json`、`048.json`
- Answer指纹 `078c3ce9c58e`：2条；`005.json`、`032.json`
- Answer指纹 `0c9425e7aeb1`：2条；`017.json`、`036.json`
- Answer指纹 `3454ed6579ef`：2条；`011.json`、`040.json`
- Answer指纹 `65e9a07ac14c`：2条；`023.json`、`047.json`
- Answer指纹 `6c04961b8610`：2条；`021.json`、`044.json`
- Answer指纹 `8ca526bcbdce`：2条；`016.json`、`030.json`
- Answer指纹 `d06ade58f17a`：2条；`014.json`、`042.json`
- Answer指纹 `d9132ad18eb3`：2条；`018.json`、`031.json`
- Answer指纹 `eeac263abd74`：2条；`007.json`、`028.json`

#### `114_05_pet_grooming`

- Answer指纹 `4dee64d546c7`：4条；`012.json`、`025.json`、`041.json`、`063.json`
- Answer指纹 `f2ab0de4ebf1`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `178e15e5a875`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `5b92499c46e9`：3条；`008.json`、`038.json`、`057.json`
- Answer指纹 `b221b701b9c6`：3条；`015.json`、`018.json`、`031.json`
- Answer指纹 `34d661833da2`：2条；`020.json`、`046.json`
- Answer指纹 `5e53299250eb`：2条；`017.json`、`036.json`
- Answer指纹 `7d535792a4d9`：2条；`007.json`、`028.json`
- Answer指纹 `a9f55e77ae88`：2条；`023.json`、`047.json`
- Answer指纹 `d03bc1b0be97`：2条；`026.json`、`045.json`
- Answer指纹 `e0ef093378c1`：2条；`022.json`、`048.json`

#### `115_06_moveout_inspection`

- Answer指纹 `ff609d1d73d0`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `060deb1015e9`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `5cccba8ed9da`：3条；`017.json`、`036.json`、`051.json`
- Answer指纹 `5cf219829690`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `e503f32c15c8`：3条；`015.json`、`023.json`、`047.json`
- Answer指纹 `0453655ad90b`：2条；`007.json`、`028.json`
- Answer指纹 `118491119e96`：2条；`001.json`、`039.json`
- Answer指纹 `2300ec130ba9`：2条；`024.json`、`048.json`
- Answer指纹 `30377c09837d`：2条；`008.json`、`038.json`
- Answer指纹 `34d661833da2`：2条；`020.json`、`046.json`
- Answer指纹 `a05f3d79cb10`：2条；`029.json`、`055.json`
- Answer指纹 `ca85a5f9d4e2`：2条；`014.json`、`042.json`
- Answer指纹 `f738d3b775c7`：2条；`009.json`、`034.json`

#### `116_07_aging_in_place`

- Answer指纹 `51199c17752f`：4条；`011.json`、`013.json`、`029.json`、`055.json`
- Answer指纹 `b8cca5e696c0`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `51d5caba72ea`：3条；`017.json`、`036.json`、`051.json`
- Answer指纹 `92fbec5050e1`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `f9693274092e`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `23b200ea72a0`：2条；`018.json`、`031.json`
- Answer指纹 `6b2b0728206c`：2条；`007.json`、`028.json`
- Answer指纹 `6f9189dfafcf`：2条；`008.json`、`038.json`
- Answer指纹 `8a33cac3b372`：2条；`014.json`、`042.json`
- Answer指纹 `919de6e419ce`：2条；`026.json`、`045.json`
- Answer指纹 `a53bc39bf91e`：2条；`039.json`、`056.json`
- Answer指纹 `a9afa92aa436`：2条；`022.json`、`048.json`
- Answer指纹 `b7023d052ebc`：2条；`015.json`、`035.json`

#### `117_08_document_destruction`

- Answer指纹 `8568770f39af`：4条；`016.json`、`030.json`、`049.json`、`068.json`
- Answer指纹 `86efe5f6b0c3`：4条；`005.json`、`011.json`、`013.json`、`029.json`
- Answer指纹 `dc6c1dfa1795`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `f215f2fc149c`：4条；`012.json`、`025.json`、`041.json`、`063.json`
- Answer指纹 `623d84cd3b6c`：3条；`017.json`、`036.json`、`051.json`
- Answer指纹 `b90f382c33e1`：3条；`008.json`、`038.json`、`057.json`
- Answer指纹 `10cba5d5f5f6`：2条；`001.json`、`056.json`
- Answer指纹 `3ad0749a4e1c`：2条；`018.json`、`031.json`
- Answer指纹 `7504cf18a1a9`：2条；`020.json`、`046.json`
- Answer指纹 `c227f4b2b8a5`：2条；`007.json`、`028.json`
- Answer指纹 `cf9dfe2fa302`：2条；`022.json`、`024.json`

#### `118_09_corporate_headshot`

- Answer指纹 `2a1e5a271415`：4条；`011.json`、`013.json`、`029.json`、`055.json`
- Answer指纹 `740568e9c9bd`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `409720fef0be`：3条；`012.json`、`025.json`、`041.json`
- Answer指纹 `e430afaef0f9`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `1eb6704a01c9`：2条；`020.json`、`046.json`
- Answer指纹 `3588b4d858e7`：2条；`001.json`、`039.json`
- Answer指纹 `3631c6128190`：2条；`006.json`、`027.json`
- Answer指纹 `61d8c54319ba`：2条；`017.json`、`036.json`
- Answer指纹 `63e0da1f2e51`：2条；`008.json`、`038.json`
- Answer指纹 `7a8d3690c9eb`：2条；`007.json`、`028.json`
- Answer指纹 `8117706b8efc`：2条；`023.json`、`047.json`
- Answer指纹 `a0b64a57b22b`：2条；`018.json`、`031.json`

#### `119_10_suit_measurement`

- Answer指纹 `62b695daed6f`：4条；`003.json`、`019.json`、`043.json`、`050.json`
- Answer指纹 `1830c3c41d30`：3条；`016.json`、`030.json`、`049.json`
- Answer指纹 `47e17b919e32`：3条；`017.json`、`025.json`、`036.json`
- Answer指纹 `66405a07ff01`：3条；`008.json`、`038.json`、`057.json`
- Answer指纹 `6e148a148a48`：3条；`021.json`、`035.json`、`044.json`
- Answer指纹 `0f742dd31657`：2条；`027.json`、`065.json`
- Answer指纹 `317a43d724e9`：2条；`001.json`、`039.json`
- Answer指纹 `43f0b776e6ce`：2条；`023.json`、`047.json`
- Answer指纹 `4a4dcfdb5d06`：2条；`022.json`、`024.json`
- Answer指纹 `7632559c4bf3`：2条；`020.json`、`046.json`
- Answer指纹 `7aed9f8caf47`：2条；`012.json`、`041.json`
- Answer指纹 `e10d5aa3d32a`：2条；`018.json`、`031.json`

## 运行目录 `kimi_k3_cot_canary_2`

- 路径：`/Users/liyong90/Desktop/sop-maze/answer_first_input_synthesis_20260813/runs/kimi_k3_cot_canary_2`
- 快照编号文件：129
- 场景数：129
- 等级分布：`{"INSUFFICIENT": 129}`
- 文件状态分布：`{"error": 25, "ok": 56, "rejected": 4, "verification_error": 44}`
- 排除原因：`{"missing_target_answer": 25}`

### 场景汇总

| 等级 | 场景 | N | U/唯一率 | 重复冗余率 | 重复样本覆盖率 | 最大簇 | Top3占比 | 随机碰撞率 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `INSUFFICIENT` | `001_bank_01_信用卡申请审批流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `002_bank_02_挂失解挂流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `003_bank_03_转账异常处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `004_bank_04_贷款咨询与申请_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `005_bank_05_理财产品购买流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `006_bank_06_投诉建议处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `007_chain_restaurant_01_麦当劳运营_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `008_chain_restaurant_02_海底捞服务_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `010_chain_restaurant_04_肯德基客服_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `011_eleme_01_饿了么外卖配送_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `012_eleme_02_饿了么商家端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `013_eleme_03_饿了么骑手端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `014_eleme_04_饿了么买药_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `015_eleme_06_饿了么会员_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `016_eleme_07_饿了么客服_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `017_eleme_08_饿了么企业版_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `018_eleme_09_饿了么营销优惠_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `019_eleme_10_饿了么物流管理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `020_eleme_11_饿了么买菜_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `021_eleme_13_饿了么跑腿_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `022_eleme_16_饿了么评价管理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `023_eleme_18_饿了么闪购_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `024_insurance_01_保险报案受理流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `025_insurance_02_理赔资料审核流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `026_insurance_03_保单变更流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `027_insurance_04_退保处理流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `028_insurance_05_保险客户投诉处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `029_insurance_06_互联网保险理赔_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `030_insurance_07_查勘定损流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `031_insurance_11_保全服务流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `032_insurance_12_反欺诈调查流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `033_jingdong_01_七天无理由退货_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `034_jingdong_02_商品质量问题退货_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `035_jingdong_03_换货补发处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `036_jingdong_04_仅退款不退货_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `037_jingdong_05_30天价保申请_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `038_jingdong_07_订单信息修改_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `039_jingdong_08_物流异常处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `040_jingdong_09_取消订单_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `041_jingdong_10_延保服务申请_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `042_jingdong_11_用户投诉处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `043_jingdong_12_白条分期问题_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `044_jingdong_13_以旧换新_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `045_jingdong_14_京东服务__v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `046_jingdong_16_企业购_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `047_jingdong_17_账户被盗申诉处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `048_jingdong_18_交易纠纷仲裁_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `049_meituan_01_外卖配送_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `050_meituan_03_酒店旅游_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `051_meituan_04_美团买菜_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `052_meituan_05_美团优选_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `054_meituan_07_美团单车_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `056_meituan_08_美团打车_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `057_meituan_09_美团买药_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `059_meituan_11_美团会员_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `060_meituan_12_美团客服_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `061_meituan_13_美团外卖商家端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `062_meituan_14_美团众包骑手端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `063_meituan_15_美团闪购商家端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `064_meituan_16_美团闪购用户端_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `065_meituan_17_美团民宿_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `067_meituan_22_美团企业版_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `068_meituan_23_美团金融_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `069_meituan_24_美团直播_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `070_payment_01_账户被盗申诉流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `071_payment_02_交易纠纷处理_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `072_payment_03_实名认证流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `073_payment_04_提现转账异常_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `074_payment_05_商家退款流程_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `075_payment_06_支付风控解冻_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `076_pdd_01_百亿补贴_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `077_pdd_02_拼团模式_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `078_pdd_03_农产品生鲜_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `080_pdd_06_多多进宝_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `081_pdd_07_多多直播_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `082_pdd_09_多多国际_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `083_pdd_10_假一赔十_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `084_pdd_13_砍价免费拿_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `085_pdd_15_省钱月卡_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `086_pdd_17_多多批发_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `088_pdd_20_多多爱消除_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `089_taobao_01_淘宝直播带货_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `090_taobao_02_闲鱼二手交易_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `091_taobao_07_淘宝联盟推广_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `092_taobao_08_discount_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `093_taobao_10_千牛商家服务_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `094_taobao_12_campaign_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `095_taobao_14_淘宝租赁_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `098_telecom_02_中国联通客服_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `099_telecom_03_中国电信客服_v28` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `100_01_reusable_container` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `101_02_cold_storage_flex_load` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `103_04_fleet_maintenance` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `106_07_night_reading_bookstore` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `111_02_moving_estimate` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `114_05_pet_grooming` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `115_06_moveout_inspection` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `117_08_document_destruction` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `118_09_corporate_headshot` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `119_10_suit_measurement` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `121_01_smart_locker` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `122_02_pet_clinic` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `123_03_public_library` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `125_05_ev_charging` | 1 | 1 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `009_chain_restaurant_03_星巴克门店运营_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `053_meituan_06_美团跑腿_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `055_meituan_08_美团外卖运营_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `058_meituan_10_美团充电宝_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `079_pdd_04_多多买菜_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `096_taobao_15_天猫奢品_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `097_telecom_01_中国移动客服_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `102_03_city_museum_pass` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `104_05_corporate_fitness_pass` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `105_06_corporate_dental_screening` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `107_08_dorm_linen_care` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `108_09_it_asset_recovery` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `109_10_overflow_fulfillment` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `110_01_piano_tuning` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `112_03_air_sampling` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `113_04_office_plant_care` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `116_07_aging_in_place` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `124_04_parking_pass` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `126_06_fitness_class` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `127_07_laundry_care` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `128_08_coworking_room` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `129_09_lab_instrument` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `130_10_cloud_printing` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `131_01_delivery_progress` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |
| `INSUFFICIENT` | `132_06_jingdong_invoice_reissue_v28` | 0 | 0 / N/A | N/A | N/A | N/A | N/A | N/A |

### 全部完全重复组

该快照没有场景出现完整 Target Answer 重复。

## 解读边界

1. `kimi_k3_cot_canary_2` 每场只有1条，因此所有场景都应是 `INSUFFICIENT`；不能用唯一率100%或最大簇100%判断坍缩。
2. 本报告可以可靠回答“完整 Target Answer 重复了多少”，不能单独回答“重复是否符合业务分支分布”。后者需要治理阶段再结合可达分支数和目标配额。
3. 没有 `target_answer`、身份错位或不满足当前 Schema 的文件不进入重复度分母，并在排除原因中明示。
4. 报告只读源文件；运行期间后来创建或替换的文件不属于本次文件名快照。
