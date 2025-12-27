"""
Generate gRPC Python code from proto files
"""

import subprocess
import sys
from pathlib import Path

def generate_grpc_code():
    """Generate Python code from proto files"""
    proto_dir = Path(__file__).parent.parent / "server_fastapi" / "proto"
    output_dir = proto_dir
    
    proto_file = proto_dir / "hft.proto"
    
    if not proto_file.exists():
        print(f"Proto file not found: {proto_file}")
        return False
    
    try:
        # Generate Python code from proto
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file),
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("gRPC code generated successfully!")
        print(f"Output directory: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating gRPC code: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("grpc_tools.protoc not found. Install with: pip install grpcio-tools")
        return False

if __name__ == "__main__":
    success = generate_grpc_code()
    sys.exit(0 if success else 1)
