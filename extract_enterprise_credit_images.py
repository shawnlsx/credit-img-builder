#!/usr/bin/env python3
"""
extract_enterprise_credit_images.py

从 企业征信查询.zip 中提取最内层的图片文件。
压缩包为三层嵌套结构：
    企业征信查询.zip                  (第一层/外层)
    └── 1-lsx-835523.zip             (第二层)
        └── 企业中征码.zip            (第三层/分类层)
            └── xxx.png              (最内层图片)

命名规则：<第二层压缩包名称(不含扩展名)>_<图片原本文件名>
例如：1-lsx-835523.zip / 企业中征码.zip / aeb2c4b1-...-77.png
      -> 1-lsx-835523_aeb2c4b1-...-77.png

用法：
    python extract_enterprise_credit_images.py [输入zip路径] [输出目录]
不传参数时使用脚本内默认路径。
"""

import io
import os
import sys
import zipfile

# 支持的图片扩展名
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')


def extract_images(outer_zip_path: str, output_dir: str) -> list:
    """
    遍历三层嵌套 zip，把最内层的图片提取到 output_dir。
    返回 (输出路径, 字节数) 列表。
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    with zipfile.ZipFile(outer_zip_path, 'r') as outer_zip:
        # 第一层 -> 第二层：1-lsx-835523.zip / 2-sds-837737.zip
        for lv2_info in outer_zip.infolist():
            if lv2_info.is_dir() or not lv2_info.filename.lower().endswith('.zip'):
                continue

            lv2_name = lv2_info.filename                       # 1-lsx-835523.zip
            lv2_base = os.path.splitext(os.path.basename(lv2_name))[0]  # 1-lsx-835523
            lv2_data = outer_zip.read(lv2_name)

            with zipfile.ZipFile(io.BytesIO(lv2_data)) as lv2_zip:
                # 第二层 -> 第三层：企业中征码.zip / 授权书.zip / 营业执照.zip
                for lv3_info in lv2_zip.infolist():
                    if lv3_info.is_dir() or not lv3_info.filename.lower().endswith('.zip'):
                        continue

                    lv3_name = lv3_info.filename
                    lv3_data = lv2_zip.read(lv3_name)

                    with zipfile.ZipFile(io.BytesIO(lv3_data)) as lv3_zip:
                        # 第三层 -> 最内层图片
                        for img_info in lv3_zip.infolist():
                            if img_info.is_dir():
                                continue
                            img_name = img_info.filename
                            ext = os.path.splitext(img_name)[1].lower()
                            if ext not in IMAGE_EXTS:
                                continue

                            img_data = lv3_zip.read(img_name)
                            img_basename = os.path.basename(img_name)

                            # 命名规则：第二层zip名_图片原本名
                            out_name = f"{lv2_base}_{img_basename}"
                            out_path = os.path.join(output_dir, out_name)

                            # 同名冲突时追加序号，避免覆盖
                            if os.path.exists(out_path):
                                counter = 1
                                stem, sfx = os.path.splitext(out_name)
                                while os.path.exists(out_path):
                                    out_name = f"{stem}_{counter}{sfx}"
                                    out_path = os.path.join(output_dir, out_name)
                                    counter += 1

                            with open(out_path, 'wb') as f:
                                f.write(img_data)

                            results.append((out_path, len(img_data)))
                            print(f"[OK] {lv2_name} / {lv3_name} / {img_basename}"
                                  f"  ->  {out_name}  ({len(img_data)} bytes)")

    return results


def main():
    # 默认路径：当前目录下的 企业征信查询.zip，输出到当前目录
    DEFAULT_ZIP = os.path.join(os.getcwd(), '企业征信查询.zip')
    DEFAULT_OUTPUT_DIR = os.getcwd()

    # 支持命令行参数覆盖
    OUTER_ZIP = DEFAULT_ZIP
    OUTPUT_DIR = DEFAULT_OUTPUT_DIR
    if len(sys.argv) >= 2:
        OUTER_ZIP = sys.argv[1]
    if len(sys.argv) >= 3:
        OUTPUT_DIR = sys.argv[2]

    if not os.path.isfile(OUTER_ZIP):
        print(f"[错误] 找不到输入文件: {OUTER_ZIP}")
        sys.exit(1)

    print(f"输入压缩包: {OUTER_ZIP}")
    print(f"输出目录  : {OUTPUT_DIR}")
    print("-" * 70)

    results = extract_images(OUTER_ZIP, OUTPUT_DIR)

    print("-" * 70)
    print(f"提取完成，共 {len(results)} 张图片，保存在: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
