# Alpaca ESP32-S3 固件发布

本仓库用于发布固件、字库、校验文件和升级说明。设备 OTA 仓库地址保持为 `alpacai/alpaca-printer-esp32`。

下载最新正式版本：[Releases](https://github.com/alpacai/alpaca-printer-esp32/releases/latest)。

| 附件 | 用途 |
| --- | --- |
| `alpaca-printer-esp32-VERSION-ota.bin` | 已有设备的网络或网页升级，仅更新应用 |
| `alpaca-printer-esp32-VERSION-full.bin` | ESP32-S3 新板首次安装，写入 `0x0`，包含分区表和中文字库 |
| `alpaca-fonts-0x410000.bin` | 独立字库 |
| `SHA256SUMS.txt` | 发布附件的 SHA-256 |

支持至少 8 MB Flash、8 MB OPI PSRAM 的 ESP32-S3。v1.2.2 及后续固件可在自动打印开启时确认安装：暂缓新接单，等待已有小票和回执完成后更新，原自动打印开关和设置保留。

固件源码在独立私有仓库维护，不作为公开 Release 附件提供。GitHub 自动生成的 Source code 压缩包仅包含这个发布仓库的说明和发布流程，不包含固件源码。

发布流程只接收编译后的三个 `.bin` 和校验文件，验证文件名单、ESP32-S3 镜像、分区大小与 SHA-256 后发布正式 Release。第三方组件许可见 `licenses/`。
