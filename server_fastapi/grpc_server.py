"""
gRPC Server Setup
Configures and starts gRPC server for high-frequency trading endpoints
"""

import logging
import asyncio
from concurrent import futures
import grpc
from grpc import aio

logger = logging.getLogger(__name__)


async def serve_grpc(port: int = 50051):
    """
    Start gRPC server
    
    Args:
        port: gRPC server port (default 50051)
    """
    try:
        # Import generated gRPC code
        try:
            from .proto import hft_pb2_grpc
            from .services.grpc.hft_service import HFTService
        except ImportError as e:
            logger.warning(f"gRPC proto files not generated: {e}")
            logger.warning("To generate proto files, run:")
            logger.warning("  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/hft.proto")
            return
        
        # Create gRPC server
        server = aio.server()
        
        # Add service
        hft_pb2_grpc.add_HFTServiceServicer_to_server(HFTService(), server)
        
        # Listen on port
        listen_addr = f"[::]:{port}"
        server.add_insecure_port(listen_addr)
        
        # Start server
        await server.start()
        logger.info(f"gRPC server started on {listen_addr}")
        
        # Wait for termination
        try:
            await server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Stopping gRPC server...")
            await server.stop(5)
            logger.info("gRPC server stopped")
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}", exc_info=True)


if __name__ == "__main__":
    # Run gRPC server
    asyncio.run(serve_grpc())
