# 电话号码验证系统使用说明

## 功能概述

本系统能够：
- 检测数据库中的空号和无效电话号码
- 为检测到的无效号码添加备注标题
- 生成详细的验证报告
- 支持批量处理大量数据

## 系统特性

### 空号检测功能
- 检测空号码
- 检测号码过短（<7位）
- 检测号码过长（>15位）
- 检测测试号码（如123456、111111等）
- 检测重复数字号码（如1111111、2222222等）

### 备注标题功能
- 自动为无效号码添加分类备注
- 支持自定义备注标题和内容
- 记录验证时间和状态

### 数据库更新功能
- 批量更新验证状态
- 添加验证字段（validation_status、validation_note等）
- 生成验证报告

## 使用方法

### 基本使用

```bash
# 运行验证系统
python phone_validation_system.py
```

### 高级使用

```bash
# 自定义批次大小和最大批次数
python phone_validation_system.py --batch_size 1000 --max_batches 20
```

### 编程接口使用

```python
from phone_validation_system import PhoneValidationSystem

# 创建验证器实例
validator = PhoneValidationSystem('people_data_final.db')

# 运行验证
success = validator.run_validation(batch_size=500, max_batches=10)

if success:
    print("验证完成")
    # 获取验证摘要
    summary = validator.get_validation_summary()
    print(f"总记录数: {summary['total_records']}")
    print(f"有效号码: {summary['valid_numbers']}")
    print(f"无效号码: {summary['invalid_numbers']}")
```

## 数据库字段说明

系统会在people表中添加以下字段：

- `validation_status`: 验证状态（valid/invalid）
- `validation_note`: 验证备注说明
- `validation_date`: 验证日期
- `custom_note_title`: 自定义备注标题
- `custom_note_content`: 自定义备注内容
- `last_modified`: 最后修改时间

## 验证结果分类

### 有效号码
- 格式正常的电话号码

### 无效号码分类
- `empty`: 空号码
- `invalid_format`: 格式无效（过短或过长）
- `test_number`: 测试号码
- `repeated_digits`: 重复数字号码

## 输出文件

系统会生成以下输出文件：

- `phone_validation.log`: 验证过程日志
- `phone_validation_report.json`: 详细验证报告（JSON格式）

## 示例输出

```
==================================================
电话号码验证摘要:
总记录数: 1,000,000
有效号码: 850,000
无效号码: 150,000
待验证: 0
本次处理: 1,000,000
本次发现无效: 150,000
==================================================

无效号码分类:
  empty: 50,000
  invalid_format: 30,000
  test_number: 40,000
  repeated_digits: 30,000
```

## 注意事项

1. 确保数据库文件存在且有读写权限
2. 系统会自动创建所需的数据库字段
3. 大数据量处理时建议适当调整批次大小
4. 验证过程会自动跳过已验证的记录
5. 建议在处理前备份数据库

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件路径是否正确
   - 确认数据库文件权限

2. **验证过程中断**
   - 重新运行系统会继续未完成的验证
   - 检查日志文件了解错误详情

3. **内存不足**
   - 减小batch_size参数
   - 增加系统内存或分批处理

## 扩展功能

系统支持以下扩展：

1. **自定义验证规则**
   - 修改validate_phone_format方法
   - 添加新的检测模式

2. **自定义备注模板**
   - 修改get_validation_remark方法
   - 添加更多备注分类

3. **导出功能**
   - 添加CSV/Excel导出
   - 生成可视化报告

## 技术支持

如需技术支持或功能定制，请联系开发团队。