"""
Handler mínimo para diagnóstico de startup no RunPod Serverless.
Sem imports de src/ — isola se o problema é nosso código ou o SDK.
"""
import runpod


def handler(job):
    return {"status": "ok", "echo": job.get("input", {})}


runpod.serverless.start({"handler": handler})
