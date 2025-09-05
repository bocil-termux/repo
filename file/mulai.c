#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main() {
    char *python_script = NULL;
    char *python_cmd = NULL;
    if (access("/data/data/com.termux/files/usr", F_OK) == 0) {
        python_script = "/data/data/com.termux/files/usr/bin/mulai.py";
        python_cmd = "python";
    } else {
        python_script = "/usr/bin/mulai.py";
        python_cmd = "python3";
    }
    if (access(python_script, F_OK) != 0) {
        fprintf(stderr, "Error: Data tidak ditemukan.\n");
        return 1;
    }
    execlp(python_cmd, python_cmd, python_script, NULL);
    perror("Error menjalankan perintah");
    return 1;
}
