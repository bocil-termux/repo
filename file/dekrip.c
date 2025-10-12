#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_PATH 4096
#define KEY_SIZE 32
#define DEFAULT_BUFFER_SIZE 4096
#define THREAD_POOL_SIZE 50
#define QUEUE_SIZE 1000
#define BATCH_SIZE 100

typedef struct {
    char *target_dir;
    unsigned char key[KEY_SIZE];
} Config;

typedef struct {
    char file_path[MAX_PATH];
    Config *config;
} ThreadData;

typedef struct {
    ThreadData *work_items[QUEUE_SIZE];
    int front, rear, count;
    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    pthread_t threads[THREAD_POOL_SIZE];
    int shutdown;
} ThreadPool;

Config config;
ThreadPool thread_pool;

void* worker_thread(void *arg);
void init_thread_pool(ThreadPool *pool);
void shutdown_thread_pool(ThreadPool *pool);
int thread_pool_submit(ThreadPool *pool, ThreadData *data);

void load_embedded_key(Config *config) {
    unsigned char embedded_key[KEY_SIZE] = {
        0x4A, 0x7F, 0xC2, 0x1D, 0x89, 0x3E, 0xB5, 0x60,
        0x2C, 0x97, 0xFA, 0x45, 0xD1, 0x6C, 0xE7, 0x7A,
        0x15, 0x88, 0xF3, 0x5E, 0xCA, 0x35, 0xA0, 0x0B,
        0x76, 0xE1, 0x4C, 0xB7, 0x22, 0x8D, 0xF8, 0x63
    };
    memcpy(config->key, embedded_key, KEY_SIZE);
    printf("Embedded key loaded\n");
}

int is_encrypted_file(const char *filename) {
    const char *dot = strrchr(filename, '.');
    return dot && strcmp(dot, ".enc") == 0;
}

void simple_decrypt(unsigned char *data, size_t len, unsigned char *key) {
    for (size_t i = 0; i < len; i++) {
        data[i] = (data[i] - key[i % KEY_SIZE] + 256) % 256;
        data[i] ^= key[i % KEY_SIZE];
    }
}

size_t get_optimal_buffer_size(const char *file_path) {
    struct stat st;
    if (stat(file_path, &st) == 0) {
        if (st.st_size > 100 * 1024 * 1024) {
            return 256 * 1024;
        } else if (st.st_size > 10 * 1024 * 1024) {
            return 64 * 1024;
        } else if (st.st_size > 1 * 1024 * 1024) {
            return 16 * 1024;
        }
    }
    return DEFAULT_BUFFER_SIZE;
}

int decrypt_file_optimized(const char *input_path, const char *output_path, Config *config) {
    FILE *in_file = fopen(input_path, "rb");
    if (!in_file) {
        printf("Failed to open input file: %s\n", input_path);
        return 0;
    }
    char signature[6];
    size_t read = fread(signature, 1, 5, in_file);
    if (read != 5 || strncmp(signature, "ENCv1", 5) != 0) {
        fclose(in_file);
        printf("Invalid encrypted file: %s\n", input_path);
        return 0;
    }
    FILE *out_file = fopen(output_path, "wb");
    if (!out_file) {
        printf("Failed to create output file: %s\n", output_path);
        fclose(in_file);
        return 0;
    }
    struct stat st;
    fstat(fileno(in_file), &st);
    size_t file_size = st.st_size;
    size_t total_bytes = 5;
    size_t buffer_size = get_optimal_buffer_size(input_path);
    unsigned char *buffer = malloc(buffer_size);
    if (!buffer) {
        fclose(in_file);
        fclose(out_file);
        return 0;
    }
    size_t bytes_read;
    while ((bytes_read = fread(buffer, 1, buffer_size, in_file)) > 0) {
        simple_decrypt(buffer, bytes_read, config->key);
        fwrite(buffer, 1, bytes_read, out_file);
        total_bytes += bytes_read;
        if (file_size > 10 * 1024 * 1024 && total_bytes % (5 * 1024 * 1024) == 0) {
            printf("  Progress: %.2f%% - %s\n", 
                   (double)total_bytes / file_size * 100, input_path);
        }
    }
    free(buffer);
    fclose(in_file);
    fclose(out_file);
    return 1;
}

void* process_encrypted_file(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    char output_path[MAX_PATH];
    strncpy(output_path, data->file_path, strlen(data->file_path) - 4);
    output_path[strlen(data->file_path) - 4] = '\0';
    pthread_mutex_lock(&thread_pool.mutex);
    printf("Decrypting: %s\n", data->file_path);
    pthread_mutex_unlock(&thread_pool.mutex);
    if (decrypt_file_optimized(data->file_path, output_path, data->config)) {
        remove(data->file_path);
        pthread_mutex_lock(&thread_pool.mutex);
        printf("Decrypted successfully: %s\n", output_path);
        pthread_mutex_unlock(&thread_pool.mutex);
    } else {
        pthread_mutex_lock(&thread_pool.mutex);
        printf("Failed to decrypt: %s\n", data->file_path);
        pthread_mutex_unlock(&thread_pool.mutex);
    }
    free(data);
    return NULL;
}

void* worker_thread(void *arg) {
    ThreadPool *pool = (ThreadPool *)arg;
    while (1) {
        pthread_mutex_lock(&pool->mutex);
        while (pool->count == 0 && !pool->shutdown) {
            pthread_cond_wait(&pool->not_empty, &pool->mutex);
        }
        if (pool->shutdown && pool->count == 0) {
            pthread_mutex_unlock(&pool->mutex);
            break;
        }
        ThreadData *data = pool->work_items[pool->front];
        pool->front = (pool->front + 1) % QUEUE_SIZE;
        pool->count--;
        pthread_cond_signal(&pool->not_full);
        pthread_mutex_unlock(&pool->mutex);
        process_encrypted_file(data);
    }
    return NULL;
}

void init_thread_pool(ThreadPool *pool) {
    pool->front = pool->rear = pool->count = 0;
    pool->shutdown = 0;
    pthread_mutex_init(&pool->mutex, NULL);
    pthread_cond_init(&pool->not_empty, NULL);
    pthread_cond_init(&pool->not_full, NULL);
    for (int i = 0; i < THREAD_POOL_SIZE; i++) {
        pthread_create(&pool->threads[i], NULL, worker_thread, pool);
    }
}

void shutdown_thread_pool(ThreadPool *pool) {
    pthread_mutex_lock(&pool->mutex);
    pool->shutdown = 1;
    pthread_cond_broadcast(&pool->not_empty);
    pthread_mutex_unlock(&pool->mutex);
    for (int i = 0; i < THREAD_POOL_SIZE; i++) {
        pthread_join(pool->threads[i], NULL);
    }
    pthread_mutex_destroy(&pool->mutex);
    pthread_cond_destroy(&pool->not_empty);
    pthread_cond_destroy(&pool->not_full);
}

int thread_pool_submit(ThreadPool *pool, ThreadData *data) {
    pthread_mutex_lock(&pool->mutex);
    while (pool->count >= QUEUE_SIZE && !pool->shutdown) {
        pthread_cond_wait(&pool->not_full, &pool->mutex);
    }
    if (pool->shutdown) {
        pthread_mutex_unlock(&pool->mutex);
        return -1;
    }
    pool->work_items[pool->rear] = data;
    pool->rear = (pool->rear + 1) % QUEUE_SIZE;
    pool->count++;
    pthread_cond_signal(&pool->not_empty);
    pthread_mutex_unlock(&pool->mutex);
    return 0;
}

void process_directory_decrypt_optimized(const char *dir_path, Config *config) {
    DIR *dir = opendir(dir_path);
    if (!dir) {
        printf("Cannot open directory: %s\n", dir_path);
        return;
    }
    struct dirent *entry;
    struct stat statbuf;
    int batch_count = 0;
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        char full_path[MAX_PATH];
        snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, entry->d_name);
        if (stat(full_path, &statbuf) == -1) {
            continue;
        }
        if (S_ISDIR(statbuf.st_mode)) {
            process_directory_decrypt_optimized(full_path, config);
        } else if (S_ISREG(statbuf.st_mode)) {
            if (is_encrypted_file(entry->d_name)) {
                ThreadData *data = malloc(sizeof(ThreadData));
                strcpy(data->file_path, full_path);
                data->config = config;
                if (thread_pool_submit(&thread_pool, data) != 0) {
                    free(data);
                    printf("Thread pool queue full, processing directly: %s\n", full_path);
                    process_encrypted_file(data);
                }
                batch_count++;
                if (batch_count % 100 == 0) {
                    printf("Submitted %d files to thread pool...\n", batch_count);
                }
            }
        }
    }
    closedir(dir);
}

char* get_home_directory() {
    char *home = getenv("HOME");
    if (home == NULL) {
        home = getenv("USERPROFILE");
    }
    return home;
}

char* build_target_path(const char *relative_path) {
    char *home = get_home_directory();
    if (home == NULL) {
        fprintf(stderr, "Error: Could not determine home directory\n");
        exit(1);
    }
    char *target_path = malloc(MAX_PATH);
    if (relative_path == NULL || strcmp(relative_path, "") == 0) {
        strcpy(target_path, home);
    } else {
        snprintf(target_path, MAX_PATH, "%s/%s", home, relative_path);
    }
    return target_path;
}

int main(int argc, char *argv[]) {
    if (argc != 3 || strcmp(argv[1], "-t") != 0) {
        printf("Usage: %s -t \"<relative_target_directory>\"\n", argv[0]);
        printf("Example: %s -t \"lab/tes\"\n", argv[0]);
        printf("Target will be relative to home directory: ~/<relative_target_directory>\n");
        return 1;
    }
    char *relative_target = argv[2];
    char *target_path = build_target_path(relative_target);
    config.target_dir = target_path;
    printf("Target directory: %s\n", config.target_dir);
    load_embedded_key(&config);
    printf("Initializing thread pool with %d threads...\n", THREAD_POOL_SIZE);
    init_thread_pool(&thread_pool);
    printf("Starting decryption...\n");
    process_directory_decrypt_optimized(config.target_dir, &config);
    printf("Waiting for thread pool to finish...\n");
    shutdown_thread_pool(&thread_pool);
    printf("Decryption completed!\n");
    free(target_path);
    return 0;
}
