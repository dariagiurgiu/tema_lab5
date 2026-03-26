#define _XOPEN_SOURCE 701
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <regex.h>
#include <errno.h>

#define FTOK_PATH "coada_msg"
#define FTOK_PROJ_ID 'B'
#define MSG_SIZE 8192
#define OUT_FILE "output.html"

struct mesg_buffer {
    long mesg_type;
    char mesg_text[MSG_SIZE];
};

int main(void) {
    key_t key;
    int msgid;
    struct mesg_buffer message;
    ssize_t rcv_len;

    key = ftok(FTOK_PATH, FTOK_PROJ_ID);
    if (key == -1) {
        perror("ftok");
        fprintf(stderr, "Creează fișierul '%s' înainte de a rula acest program.\n", FTOK_PATH);
        return 1;
    }
    printf("ftok key = %d\n", (int)key);
    
    msgid = msgget(key, 0666 | IPC_CREAT);
    if (msgid == -1) {
        perror("msgget");
        return 2;
    }

    memset(&message, 0, sizeof(message));
    rcv_len = msgrcv(msgid, &message, sizeof(message.mesg_text), 1, 0);
    if (rcv_len == -1) {
        perror("msgrcv");
        return 3;
    }

    if (rcv_len >= MSG_SIZE) rcv_len = MSG_SIZE - 1;
    message.mesg_text[rcv_len] = '\0';

    regex_t re_title, re_p;
    int rc1 = regcomp(&re_title, "<title>[^<]+</title>", REG_ICASE | REG_EXTENDED);
    int rc2 = regcomp(&re_p, "<p>[^<]+</p>", REG_ICASE | REG_EXTENDED);
    if (rc1 || rc2) {
        fprintf(stderr, "regcomp failed\n");
        if (!rc1) regfree(&re_title);
        if (!rc2) regfree(&re_p);
        return 4;
    }

    int match_title = (regexec(&re_title, message.mesg_text, 0, NULL, 0) == 0);
    int match_p = (regexec(&re_p, message.mesg_text, 0, NULL, 0) == 0);

    regfree(&re_title);
    regfree(&re_p);

    if (!match_title || !match_p) {
        fprintf(stderr, "Validation failed: match_title=%d match_p=%d\n", match_title, match_p);
        FILE *ferr = fopen("validation_error.txt", "w");
        if (ferr) {
            fprintf(ferr, "Validation failed: match_title=%d match_p=%d\n", match_title, match_p);
            fprintf(ferr, "Received (truncated to 2000 chars):\n%.2000s\n", message.mesg_text);
            fclose(ferr);
        }
        return 5;
    }

    FILE *fout = fopen(OUT_FILE, "wb");
    if (!fout) {
        perror("fopen output");
        return 6;
    }
    size_t written = fwrite(message.mesg_text, 1, rcv_len, fout);
    fclose(fout);
    printf("Mesaj validat și scris în %s (%zu bytes)\n", OUT_FILE, written);
`
    return 0;
}

