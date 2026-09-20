# Results
n=1000000000, parts=16

| Method | ms | Speedup |
|--------|----|---------|
| Single-threaded | 1087.42 | 1.00x |
| Thread + join | 132.59 | 8.20x |
| ThreadPoolExecutor | 146.54 | 7.42x |
| ProcessPoolExecutor | 799.20 | 1.36x |

## Conclusions
- Thread + join: 8.20x (> ThreadPoolExecutor, > ProcessPoolExecutor)
- ThreadPoolExecutor: 7.42x (< Thread + join, > ProcessPoolExecutor)
- ProcessPoolExecutor: 1.36x (< Thread + join, < ThreadPoolExecutor)

Fastest: Thread + join (132.59 ms).
