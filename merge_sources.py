#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merge_sources.py
  -a : 스크립트 위치 기준으로 모든 하위 디렉토리의 소스/텍스트 파일을 합쳐 document.txt 생성
  -d <DIRECTORY_NAME> : 지정한 하위 디렉토리 내부(재귀) 파일만 합쳐 document.txt 생성

출력 포맷:
-- relative/path/to/file.ext

<파일 내용>

주의:
- 바이너리/대용량 아티팩트가 섞이지 않도록 확장자 화이트리스트를 사용합니다.
- .git, node_modules, build, bin 등 일반적인 빌드/의존 디렉토리는 자동 제외합니다.
"""

from __future__ import annotations
import argparse
from pathlib import Path

# 포함할 파일 확장자/파일명 (필요시 자유롭게 추가하세요)
WHITELIST_EXTS = {
    ".c", ".h", ".hpp", ".hh", ".hxx", ".ipp",
    ".cpp", ".cc", ".cxx", ".inl", ".ixx",
    ".cs", ".java", ".kt",
    ".ts", ".tsx", ".js", ".jsx",
    ".py", ".rs", ".go", ".swift",
    ".m", ".mm", ".lua", ".sh", ".bat", ".ps1",
    ".cmake", ".proto", ".sql",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".txt", ".md", ".json", ".csv",
    ".f90", ".f95", ".f03", ".f08", ".for", ".f", ".ftn",
    ".asm", ".s",
    ".vert", ".frag", ".glsl", ".hlsl", ".metal",
    ".make",
}
WHITELIST_BARE_NAMES = {"Makefile", "CMakeLists.txt"}

# 제외할 디렉토리
EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".vs",
    "node_modules", "dist", "out", "build", "target", "bin", "obj",
    "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    "DerivedData", "Pods"
}

OUTPUT_FILENAME = "document.txt"


def is_allowed_file(path: Path) -> bool:
    if path.name in WHITELIST_BARE_NAMES:
        return True
    return path.suffix.lower() in WHITELIST_EXTS


def should_skip_dir(path: Path) -> bool:
    return path.name in EXCLUDE_DIRS


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    # rglob으로 모두 탐색하되, 중간 디렉토리 제외를 적용
    for p in root.rglob("*"):
        if p.is_dir():
            # rglob 결과에서 디렉토리도 나오므로, 제외 디렉토리는 내부 탐색 자체가 안 되도록 패스
            # (Path.rglob은 중간에서 탐색 중단하기 어렵기 때문에 필터링만 수행)
            continue
        if any(should_skip_dir(parent) for parent in p.parents if parent != root):
            continue
        if is_allowed_file(p):
            files.append(p)
    # 경로 기준 정렬(일관된 출력)
    files.sort(key=lambda x: str(x).lower())
    return files


def write_merged(root: Path, files: list[Path], out_file: Path) -> None:
    rel_base = root
    with out_file.open("w", encoding="utf-8", newline="\n") as fw:
        for i, f in enumerate(files):
            rel = f.relative_to(rel_base).as_posix()
            fw.write(f"-- {rel}\n\n")
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                text = f"<<ERROR READING FILE: {e}>>"
            fw.write(text.rstrip() + "\n")
            if i != len(files) - 1:
                fw.write("\n")  # 파일 간 공백줄


def main():
    parser = argparse.ArgumentParser(
        description="하위 소스/텍스트 파일들을 하나의 document.txt로 병합"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-a", "--all", action="store_true",
                      help="스크립트 위치 기준 모든 하위 디렉토리 대상")
    mode.add_argument("-d", "--dir", dest="dir_name", metavar="DIRECTORY_NAME",
                      help="지정한 하위 디렉토리만 대상")
    parser.add_argument("-o", "--output", default=OUTPUT_FILENAME,
                        help=f"출력 파일명 (기본: {OUTPUT_FILENAME})")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent

    if args.all:
        root = script_dir
    else:
        root = (script_dir / args.dir_name).resolve()
        if not root.exists() or not root.is_dir():
            raise SystemExit(f"[에러] 디렉토리를 찾을 수 없습니다: {root}")

    out_path = (script_dir / args.output).resolve()

    # 출력 파일 자신이 병합 대상에 섞이지 않도록 사전 제거(또는 후처리 제외)
    if out_path.exists():
        try:
            out_path.unlink()
        except Exception:
            pass

    files = iter_source_files(root)
    write_merged(root, files, out_path)
    print(f"[완료] {len(files)}개 파일을 병합했습니다 -> {out_path}")


if __name__ == "__main__":
    main()
