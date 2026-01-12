#!/bin/bash

# 设置原始文件名 / Set the original filename
source_file="135_69_L.jpg"

# 循环 36 次 / Loop 36 times
for i in {01..36}; do
    # 使用占位符保持文件名整齐 / Use placeholders to keep filenames tidy
    cp "$source_file" "photo_$i.jpg"
done

echo "复制完成！/ Copy completed!"