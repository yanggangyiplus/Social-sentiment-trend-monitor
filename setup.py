"""
Social Sentiment & Trend Monitor 패키지 설정 파일
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="social-sentiment-trend-monitor",
    version="0.1.0",
    author="yanggangyi",
    author_email="your.email@example.com",
    description="실시간 감정 분석 & 트렌드 변화 탐지 서비스",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yanggangyiplus/Social-sentiment-trend-monitor",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
)

