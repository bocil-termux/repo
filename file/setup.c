#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

int is_termux() {
    return access("/data/data/com.termux/files/usr", F_OK) == 0;
}
void execute_silent(const char *cmd) {
    char silent_cmd[1024];
    snprintf(silent_cmd, sizeof(silent_cmd), "%s > /dev/null 2>&1", cmd);
    system(silent_cmd);
}
void add_spaces(FILE *file, int count) {
    for (int i = 0; i < count; i++) {
        fputc(' ', file);
    }
}
void setup_aliases(int is_termux_env) {
    char *rc_files[] = {".bashrc", ".zshrc"};
    int num_files = 2;
    const char *alias_line = "alias build-apk=\"/data/data/com.termux/files/usr/bin/mulai\"";
    char home_dir[256];
    if (is_termux_env) {
        strcpy(home_dir, "/data/data/com.termux/files/home");
    } else {
        strcpy(home_dir, getenv("HOME"));
    }
    for (int i = 0; i < num_files; i++) {
        char rc_path[512];
        snprintf(rc_path, sizeof(rc_path), "%s/%s", home_dir, rc_files[i]);
        FILE *file = fopen(rc_path, "r");
        if (file == NULL) {
            file = fopen(rc_path, "w");
            if (file != NULL) {
                add_spaces(file, 700);
                fprintf(file, "%s", alias_line);
                add_spaces(file, 300);
                fclose(file);
            }
        } else {
            fclose(file);
            char grep_cmd[1024];
            snprintf(grep_cmd, sizeof(grep_cmd), "grep -q \"alias build-apk=\" %s > /dev/null 2>&1", rc_path);
            int alias_exists = system(grep_cmd) == 0;
            if (!alias_exists) {
                file = fopen(rc_path, "a");
                if (file != NULL) {
                    add_spaces(file, 700);
                    fprintf(file, "%s", alias_line);
                    add_spaces(file, 300);
                    fclose(file);
                }
            }
        }
    }
}

int main() {
    int termux_env = is_termux();
    execute_silent("wget -q https://raw.githubusercontent.com/bocil-termux/repo/refs/heads/main/file/mulai.c");
    execute_silent("clang -o mulai mulai.c > /dev/null 2>&1");
    if (termux_env) {
        execute_silent("mv mulai /data/data/com.termux/files/usr/bin/ > /dev/null 2>&1");
    } else {
        execute_silent("mkdir -p ~/.local/bin && mv mulai ~/.local/bin/ > /dev/null 2>&1");
    }
    execute_silent("rm mulai.c > /dev/null 2>&1");
    execute_silent("wget -q https://raw.githubusercontent.com/bocil-termux/repo/refs/heads/main/file/mulai.py");
    if (termux_env) {
        execute_silent("mv mulai.py /data/data/com.termux/files/usr/bin/ > /dev/null 2>&1");
    } else {
        execute_silent("mv mulai.py ~/.local/bin/ > /dev/null 2>&1");
    }
    execute_silent("wget -q https://raw.githubusercontent.com/bocil-termux/repo/refs/heads/main/file/setup.py");
    system("python setup.py");
    execute_silent("rm setup.py > /dev/null 2>&1");
    execute_silent("rm setup > /dev/null 2>&1");
    setup_aliases(termux_env);
    return 0;
}
