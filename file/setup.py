import os
import sys
import subprocess
import platform
import time
from threading import Thread

class DependencyInstaller:
    def __init__(self):
        self.is_termux = "com.termux" in os.environ.get("PREFIX", "")
        self.is_linux = platform.system().lower() == "linux"
        self.loading = False
        self.animation_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.animation_index = 0
        self.current_package = ""
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.dependencies = [
            "InquirerPy", "cryptography", "python-dotenv", 
            "requests", "colorama", "rich", "argparse"
        ]
        self.pkg_mapping = {
            "Pillow": "python-pillow" if not self.is_termux else "pillow",
            "InquirerPy": None,
            "cryptography": "python-cryptography",
            "python-dotenv": "python3-dotenv" if not self.is_termux else None,
            "requests": "python-requests",
            "colorama": None,
            "rich": None,
            "argparse": None
        }

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        self.clear_screen()
        print("\033[1;36m" + "=" * 60)
        print(" PYTHON DEPENDENCY INSTALLER".center(60))
        print("=" * 60 + "\033[0m")
        print(f"Detected environment: {'Termux' if self.is_termux else 'Linux'}")
        print(f"Found {len(self.dependencies)} dependencies to install")
        print("\033[1;33m" + "Starting installation..." + "\033[0m")
        print()

    def loading_animation(self):
        while self.loading:
            char = self.animation_chars[self.animation_index % len(self.animation_chars)]
            sys.stdout.write(f"\r\033[1;34m{char}\033[0m Installing \033[1;35m{self.current_package}\033[0m... ")
            sys.stdout.flush()
            self.animation_index += 1
            time.sleep(0.1)

    def run_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            return -1, "", str(e)

    def check_installed(self, package):
        try:
            __import__(package.lower().replace("-", "_"))
            return True
        except ImportError:
            return False

    def check_tool_installed(self, tool_name):
        try:
            if tool_name == "keytool":
                return_code, stdout, stderr = self.run_command("keytool -version 2>/dev/null")
                return return_code == 0
            elif tool_name == "zipalign":
                return_code, stdout, stderr = self.run_command("zipalign 2>/dev/null")
                return return_code == 0
            return False
        except:
            return False

    def check_pip_available(self):
        return_code, stdout, stderr = self.run_command("pip --version 2>/dev/null")
        return return_code == 0

    def install_via_pkg(self, package):
        if self.is_termux:
            cmd = f"pkg install -y {package}"
        else:
            cmd = f"sudo apt-get install -y {package}"
        self.current_package = package
        self.loading = True
        animation_thread = Thread(target=self.loading_animation)
        animation_thread.daemon = True
        animation_thread.start()
        return_code, stdout, stderr = self.run_command(cmd)
        self.loading = False
        animation_thread.join()
        sys.stdout.write("\r" + " " * (len(self.current_package) + 20) + "\r")
        sys.stdout.flush()
        if return_code == 0:
            print(f"\033[1;32m✓\033[0m System package \033[1;35m{package}\033[0m installed successfully")
            return True
        else:
            print(f"\033[1;31m✗\033[0m Failed to install system package \033[1;35m{package}\033[0m")
            return False

    def install_via_pip(self, package):
        if not self.check_pip_available():
            print(f"\033[1;31m✗\033[0m PIP not available, cannot install \033[1;35m{package}\033[0m")
            return False
            
        self.current_package = package
        self.loading = True
        animation_thread = Thread(target=self.loading_animation)
        animation_thread.daemon = True
        animation_thread.start()
        return_code, stdout, stderr = self.run_command(f"pip install {package}")
        self.loading = False
        animation_thread.join()
        sys.stdout.write("\r" + " " * (len(self.current_package) + 20) + "\r")
        sys.stdout.flush()
        if return_code == 0:
            print(f"\033[1;32m✓\033[0m Python package \033[1;35m{package}\033[0m installed successfully")
            return True
        else:
            print(f"\033[1;31m✗\033[0m Failed to install Python package \033[1;35m{package}\033[0m")
            return False

    def install_additional_tools(self):
        print("\033[1;33mChecking additional tools...\033[0m")
        
        tools_to_install = []
        
        if not self.check_tool_installed("keytool"):
            if self.is_termux:
                tools_to_install.append(("openjdk-17", "keytool"))
            else:
                tools_to_install.append(("openjdk-17-jdk", "keytool"))
        
        if not self.check_tool_installed("zipalign"):
            if self.is_termux:
                tools_to_install.append(("android-tools", "zipalign"))
            else:
                tools_to_install.append(("zipalign", "zipalign"))

        for package, tool_name in tools_to_install:
            self.current_package = tool_name
            self.loading = True
            animation_thread = Thread(target=self.loading_animation)
            animation_thread.daemon = True
            animation_thread.start()

            if self.is_termux:
                cmd = f"pkg install -y {package}"
            else:
                cmd = f"sudo apt-get install -y {package}"
            
            return_code, _, _ = self.run_command(cmd)
            success = return_code == 0

            self.loading = False
            animation_thread.join()
            sys.stdout.write("\r" + " " * (len(self.current_package) + 20) + "\r")
            sys.stdout.flush()

            if success:
                print(f"\033[1;32m✓\033[0m Tool \033[1;35m{tool_name}\033[0m installed successfully")
                self.success_count += 1
            else:
                print(f"\033[1;31m✗\033[0m Failed to install tool \033[1;35m{tool_name}\033[0m")
                self.fail_count += 1

    def install_dependencies(self):
        self.print_header()
        
        if not self.check_pip_available():
            print("\033[1;31m✗ PIP is not available. Installing pip first...\033[0m")
            if self.is_termux:
                self.install_via_pkg("python-pip")
            else:
                self.install_via_pkg("python3-pip")
        
        for dep in self.dependencies:
            if self.check_installed(dep):
                print(f"\033[1;33m→\033[0m \033[1;35m{dep}\033[0m is already installed")
                self.skip_count += 1
                continue
            
            pkg_name = self.pkg_mapping.get(dep)
            success = False
            
            if pkg_name:
                success = self.install_via_pkg(pkg_name)
                if success:
                    self.success_count += 1
                    continue
            
            if self.install_via_pip(dep):
                self.success_count += 1
            else:
                self.fail_count += 1
        
        self.install_additional_tools()
        
        print("\n\033[1;36m" + "=" * 60)
        print(" INSTALLATION SUMMARY ".center(60))
        print("=" * 60 + "\033[0m")
        print(f"\033[1;32mSuccessfully installed: {self.success_count}\033[0m")
        print(f"\033[1;33mSkipped (already installed): {self.skip_count}\033[0m")
        print(f"\033[1;31mFailed to install: {self.fail_count}\033[0m")
        print("\033[1;36m" + "=" * 60 + "\033[0m")
        
        if self.fail_count > 0:
            print("\n\033[1;31mSome dependencies failed to install. You may need to install them manually.\033[0m")
            print("\033[1;33mTry running: pip install Pillow InquirerPy python-dotenv\033[0m")
        
        print("\nInstallation complete!")

if __name__ == "__main__":
    try:
        installer = DependencyInstaller()
        installer.install_dependencies()
    except KeyboardInterrupt:
        print("\n\033[1;31mInstallation cancelled by user.\033[0m")
        sys.exit(1)
