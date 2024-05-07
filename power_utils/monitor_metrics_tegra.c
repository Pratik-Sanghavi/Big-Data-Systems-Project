#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>
#include<time.h>

int validate_input(const char* input) {
    return strstr(input, "RAM") && strstr(input, "CPU") && strstr(input, "VDD_SYS_GPU");
}

int main(int argc, char* argv[]){
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <interval>\n", argv[0]);
        return EXIT_FAILURE;
    }

    int pipefd[2];
    pid_t pid;
    char buffer[1024];

    char *args[] = {"sudo", "/usr/bin/tegrastats", "--interval", argv[1], NULL};

    if (pipe(pipefd) == -1) {
        perror("pipe");
        return EXIT_FAILURE;
    }
    pid = fork();
    if (pid == -1) {
        perror("fork");
        return EXIT_FAILURE;
    }

    if (pid == 0) {
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[1]);

        execvp("sudo", args);
        perror("execvp");
        exit(EXIT_FAILURE);
    } else {
        close(pipefd[1]);

        FILE *file = fopen("./system_stats.csv", "w");
        if (file == NULL) {
            perror("Failed to create the file");
            return EXIT_FAILURE;
        }

        // Write CSV headers
        fprintf(file, "Time,RAM Used (MB),RAM Total (MB),CPU1 (%%),CPU2 (%%),CPU3 (%%),CPU4 (%%),CPU5 (%%),CPU6 (%%),PLL Temp (°C),MCPU Temp (°C),PMIC Temp (°C),Tboard Temp (°C),GPU Temp (°C),BCPU Temp (°C),Thermal Temp (°C),Tdiode Temp (°C),VDD_SYS_GPU (current/max),VDD_SYS_SOC (current/max),VDD_4V0_WIFI (current/max),VDD_IN (current/max),VDD_SYS_CPU (current/max),VDD_SYS_DDR (current/max)\n");

        int ram_used, ram_total;
        int cpu_usage[6];
        float pll_temp, mcpu_temp, pmic_temp, tboard_temp, gpu_temp, bcpu_temp, thermal_temp, tdiode_temp;
        int vdd_sys_gpu[2], vdd_sys_soc[2], vdd_4v0_wifi[2], vdd_in[2], vdd_sys_cpu[2], vdd_sys_ddr[2];


        while (read(pipefd[0], buffer, sizeof(buffer) - 1) > 0) {
            buffer[sizeof(buffer) - 1] = '\0'; // Ensure null-termination
            if (!validate_input(buffer)) {
                continue;
            }
            sscanf(strstr(buffer, "RAM"), "RAM %d/%dMB", &ram_used, &ram_total);
            char* cpu_part = strstr(buffer, "CPU [");
            sscanf(cpu_part, "CPU [%d%%@%*d,%d%%@%*d,%d%%@%*d,%d%%@%*d,%d%%@%*d,%d%%@%*d]", 
                            &cpu_usage[0], &cpu_usage[1], &cpu_usage[2], &cpu_usage[3], &cpu_usage[4], &cpu_usage[5]);
            sscanf(strstr(buffer, "PLL@"), "PLL@%fC MCPU@%fC PMIC@%fC Tboard@%fC GPU@%fC BCPU@%fC thermal@%fC Tdiode@%fC", 
                            &pll_temp, &mcpu_temp, &pmic_temp, &tboard_temp, &gpu_temp, &bcpu_temp, &thermal_temp, &tdiode_temp);

            sscanf(strstr(buffer, "VDD_SYS_GPU"), "VDD_SYS_GPU %d/%d VDD_SYS_SOC %d/%d VDD_4V0_WIFI %d/%d VDD_IN %d/%d VDD_SYS_CPU %d/%d VDD_SYS_DDR %d/%d",
                            &vdd_sys_gpu[0], &vdd_sys_gpu[1], 
                            &vdd_sys_soc[0], &vdd_sys_soc[1], 
                            &vdd_4v0_wifi[0], &vdd_4v0_wifi[1], 
                            &vdd_in[0], &vdd_in[1], 
                            &vdd_sys_cpu[0], &vdd_sys_cpu[1], 
                            &vdd_sys_ddr[0], &vdd_sys_ddr[1]);
            time_t tm;
            time(&tm);
            char *t = ctime(&tm);
            if (t[strlen(t)-1] == '\n') t[strlen(t)-1] = '\0';
            fprintf(file, "%s,%d,%d,", t, ram_used, ram_total);
            for (int i = 0; i < 6; i++) {
                fprintf(file, "%d,", cpu_usage[i]);
            }
            fprintf(file, "%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,", pll_temp, mcpu_temp, pmic_temp, tboard_temp, gpu_temp, bcpu_temp, thermal_temp, tdiode_temp);
            
            fprintf(file, "%d/%d,%d/%d,%d/%d,%d/%d,%d/%d,%d/%d\n", 
                            vdd_sys_gpu[0], vdd_sys_gpu[1], vdd_sys_soc[0], vdd_sys_soc[1], vdd_4v0_wifi[0], vdd_4v0_wifi[1], 
                            vdd_in[0], vdd_in[1], vdd_sys_cpu[0], vdd_sys_cpu[1], vdd_sys_ddr[0], vdd_sys_ddr[1]);
        }

        fclose(file);
        close(pipefd[0]);
        wait(NULL);
    }
    return 0;
}