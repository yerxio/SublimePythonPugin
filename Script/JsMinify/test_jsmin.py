import jsmin
import sys

# 用法: python test_jsmin.py input.js output.js

def main():
    if len(sys.argv) != 3:
        print("用法: python test_jsmin.py <输入文件> <输出文件>")
        return
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        js_code = f.read()

    minified = extreme_minify(js_code)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(minified)
    print("压缩完成，结果已写入:", output_file)

def extreme_minify(js_code):
    minified = jsmin.jsmin(js_code)
    return ''.join(line.strip() for line in minified.splitlines())


if __name__ == "__main__":
    main() 