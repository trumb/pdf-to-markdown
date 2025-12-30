# PDF Sandboxing

PDF processing security through subprocess isolation.

## Overview

All PDF processing occurs in isolated subprocesses to protect the main application from malicious PDF files. This sandboxing approach provides defense-in-depth security.

## Threat Model

### Threats Mitigated

1. **Malicious PDF Exploits**
   - Buffer overflows in PDF libraries
   - Code execution vulnerabilities
   - Memory corruption attacks

2. **Resource Exhaustion**
   - Infinite loops in PDF processing
   - Memory bombs (massive memory allocation)
   - CPU exhaustion attacks

3. **System Compromise**
   - Filesystem access attempts
   - Network connections
   - Privilege escalation

## Sandbox Implementation

### Process Isolation

```python
# Subprocess execution
import subprocess
import resource

def process_pdf_in_sandbox(bytesContent: bytes) -> str:
    """Process PDF in isolated subprocess."""
    
    # Create isolated subprocess
    process = subprocess.Popen(
        ['python', '-m', 'pdf2md.worker'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # Isolate from parent
        preexec_fn=set_resource_limits
    )
    
    # Process with timeout
    try:
        stdout, stderr = process.communicate(
            input=bytesContent,
            timeout=300  # 5 minute timeout
        )
    except subprocess.TimeoutExpired:
        process.kill()
        raise PDFProcessingTimeout("PDF processing exceeded timeout")
    
    return stdout.decode('utf-8')
```

### Resource Limits

Resource limits are enforced on subprocess:

| Resource | Limit | Purpose |
|----------|-------|---------|
| Memory | 2 GB | Prevent memory bombs |
| CPU Time | 300 seconds | Prevent infinite loops |
| File Size | 100 MB input | Limit processing size |
| Processes | 1 | No process spawning |

**Implementation**:
```python
import resource

def set_resource_limits():
    """Set resource limits for PDF processing subprocess."""
    # Memory limit: 2 GB
    resource.setrlimit(
        resource.RLIMIT_AS,
        (2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024)
    )
    
    # CPU time limit: 5 minutes
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (300, 300)
    )
    
    # No process spawning
    resource.setrlimit(
        resource.RLIMIT_NPROC,
        (1, 1)
    )
```

## Security Benefits

### 1. Process Isolation

**Protection**: Subprocess crash doesn't affect main application

**Example**:
```
Main API (port 8000)
    ↓
    Creates isolated subprocess
    ↓
PDF Processing Subprocess
    ↓
    Crashes due to malicious PDF
    ↓
Main API continues serving requests
```

### 2. Resource Containment

**Protection**: Resource exhaustion limited to subprocess

**Scenarios**:
- PDF with infinite loop → subprocess killed after timeout
- Memory bomb PDF → subprocess killed at 2 GB limit
- CPU-intensive PDF → terminated after 5 minutes

### 3. No Network Access

**Protection**: Subprocess has no network capabilities

Prevents:
- Data exfiltration
- C2 communication
- Network-based attacks

### 4. Limited Filesystem Access

**Protection**: Subprocess runs with minimal filesystem permissions

- Read: Only input PDF (via stdin)
- Write: Only output markdown (via stdout)
- No arbitrary file access

## Error Handling

### Timeout Protection

```python
try:
    result = process_pdf_with_timeout(pdf_bytes, timeout=300)
except subprocess.TimeoutExpired:
    logger.warning(f"PDF processing timeout after 300s")
    return {
        "status": "failed",
        "error": "Processing timeout - PDF may be malicious or too complex"
    }
```

### Memory Limit Exceeded

```python
if process.returncode == -9:  # SIGKILL (OOM)
    logger.error(f"PDF processing killed - memory limit exceeded")
    return {
        "status": "failed",
        "error": "Memory limit exceeded - PDF may contain memory bomb"
    }
```

### Crash Recovery

```python
if process.returncode != 0:
    logger.error(f"PDF processing failed: {stderr.decode()}")
    return {
        "status": "failed",
        "error": "PDF processing error - file may be corrupted or malicious"
    }
```

## Configuration

### Environment Variables

```bash
# .env
PDF_PROCESSING_TIMEOUT=300  # seconds
PDF_MEMORY_LIMIT=2048  # MB
PDF_MAX_FILE_SIZE=100  # MB
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G  # Main app + subprocesses
          cpus: '2.0'
```

## Monitoring

### Subprocess Metrics

Monitor subprocess behavior:

```python
# Log subprocess metrics
logger.info(f"PDF processing started", extra={
    "job_id": job_id,
    "file_size": len(pdf_bytes),
    "timeout": 300
})

# After processing
logger.info(f"PDF processing complete", extra={
    "job_id": job_id,
    "duration_seconds": duration,
    "memory_peak_mb": memory_peak,
    "exit_code": process.returncode
})
```

### Alerts

Configure alerts for:
- High timeout rate (>5%)
- Memory limit exceeded (>1%)
- Frequent subprocess crashes
- Abnormal processing times

## Best Practices

### 1. Always Use Subprocess

Never process PDFs in the main application process:

❌ **Bad**:
```python
# Direct processing in main app
result = pdfplumber.open(BytesIO(pdf_bytes))
```

✅ **Good**:
```python
# Subprocess isolation
result = process_in_subprocess(pdf_bytes)
```

### 2. Set Appropriate Timeouts

```python
# Adjust based on typical processing time
TIMEOUT = max(typical_time * 3, 60)  # At least 60 seconds
```

### 3. Log Suspicious Activity

```python
if duration > EXPECTED_DURATION * 2:
    logger.warning(f"Unusually long processing time: {duration}s")

if memory_usage > EXPECTED_MEMORY * 2:
    logger.warning(f"High memory usage: {memory_usage}MB")
```

### 4. Validate Input

```python
# Validate before subprocess
if len(pdf_bytes) > MAX_FILE_SIZE:
    raise PDFTooLargeError("PDF exceeds maximum size")

if not is_valid_pdf_header(pdf_bytes):
    raise InvalidPDFError("File is not a valid PDF")
```

## Testing Sandbox

### Test Malicious PDF Handling

```python
def test_malicious_pdf_timeout():
    """Test that infinite loop PDF is terminated."""
    malicious_pdf = create_infinite_loop_pdf()
    
    with pytest.raises(PDFProcessingTimeout):
        process_pdf(malicious_pdf)

def test_memory_bomb_pdf():
    """Test that memory bomb PDF is killed."""
    memory_bomb = create_memory_bomb_pdf()
    
    with pytest.raises(PDFProcessingError):
        process_pdf(memory_bomb)
```

### Verify Resource Limits

```python
def test_resource_limits_applied():
    """Verify subprocess has resource limits."""
    # Process PDF and check limits were applied
    result = process_pdf(valid_pdf)
    
    assert result.memory_usage < 2048  # MB
    assert result.cpu_time < 300  # seconds
```

## Limitations

### What Sandbox Does NOT Protect Against

1. **Legitimate Complex PDFs**
   - Very large PDFs may still timeout
   - Complex layouts may require more resources

2. **DoS via Volume**
   - High volume of requests can still overload system
   - Use rate limiting for DoS protection

3. **Logic Bugs**
   - Sandbox doesn't protect against application logic bugs
   - Code review and testing still required

## Performance Considerations

### Subprocess Overhead

- **Startup**: ~50ms per subprocess
- **Memory**: ~50MB base memory per subprocess
- **I/O**: stdin/stdout for data transfer

### Optimization Strategies

1. **Pool Pattern**: Not recommended (defeats isolation purpose)
2. **Parallel Processing**: Safe - each subprocess isolated
3. **Async I/O**: Use for non-blocking subprocess communication

## Troubleshooting

### Issue: All PDFs timing out

**Cause**: Timeout too short

**Solution**:
```bash
PDF_PROCESSING_TIMEOUT=600  # Increase to 10 minutes
```

### Issue: Subprocess crashes frequently

**Cause**: Insufficient memory limit

**Solution**:
```bash
PDF_MEMORY_LIMIT=4096  # Increase to 4 GB
```

### Issue: "Too many processes" error

**Cause**: Subprocess cleanup failure

**Solution**: Ensure proper cleanup:
```python
try:
    result = process_pdf(pdf_bytes)
finally:
    if process and process.poll() is None:
        process.kill()
```

## Security Checklist

- [ ] All PDF processing in subprocess
- [ ] Resource limits configured
- [ ] Timeouts set appropriately
- [ ] Error handling for all failure modes
- [ ] Logging for suspicious activity
- [ ] Monitoring alerts configured
- [ ] Regular testing with edge cases
- [ ] Input validation before processing

---

Subprocess sandboxing is a critical security layer. Do not bypass or disable it in production.